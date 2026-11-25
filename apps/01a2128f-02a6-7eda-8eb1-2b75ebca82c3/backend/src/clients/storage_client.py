"""
Shared file-storage client for backend services.

This wrapper centralizes object-storage selection so file contents live in the
customer's cloud bucket instead of the database or the local filesystem. The
runtime is ephemeral — anything written to disk is gone after the request and
storing bytes in Postgres bloats the database — so user uploads and generated
files must go through this client:
- Workspace: a local filesystem stand-in so builds and `make validate-api` run
  without cloud credentials.
- Sandbox and Production GCP apps: Google Cloud Storage.
- Sandbox and Production AWS apps: S3.
- Sandbox and Production Azure apps: Azure Blob Storage.

Every object is stored under `apps/{APP_ID}/files/` in the single artifacts
bucket, matching the per-app least-privilege grant the platform provisions, so
app code can neither see the bucket name nor reach another app's objects.

Persist the file key plus metadata (filename, content type, size, owner) in
your database — never store file bytes in a column. Stream a download back with
`StreamingResponse(io.BytesIO(open_file(key)), media_type=..., headers=...)`.
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

import boto3
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobServiceClient, ContentSettings
from botocore.exceptions import ClientError
from google.api_core.exceptions import NotFound as GCSNotFound
from google.cloud import storage

from .azure_credential import build_azure_credential

# The Azure SDK logs every request and response header at INFO, which the
# app's INFO root logger would record for each file read or write; keep only
# its warnings and errors.
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(
    logging.WARNING
)

_SUPPORTED_PROVIDERS = {"gcp", "aws", "azure"}
_OBJECT_PREFIX_TEMPLATE = "apps/{app_id}/files/"


def _get_required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _is_workspace_runtime() -> bool:
    return os.environ.get("IS_WORKSPACE", "").strip().lower() == "true"


def _get_provider() -> str:
    provider = _get_required_env("CLOUD_PROVIDER").lower()
    if provider not in _SUPPORTED_PROVIDERS:
        raise RuntimeError(f"Unsupported CLOUD_PROVIDER: {provider}")
    return provider


def _normalize_key(key: str) -> str:
    """Validate a caller-supplied logical key (e.g. `uploads/<uuid>/<name>`).

    Leading slashes are stripped and `..` segments are rejected so a key can
    never escape the app's `apps/{APP_ID}/files/` prefix.
    """
    normalized = key.strip().lstrip("/")
    if not normalized:
        raise RuntimeError("file key is required")
    if ".." in Path(normalized).parts:
        raise RuntimeError(f"invalid file key: {key}")
    return normalized


def _is_s3_not_found(err: ClientError) -> bool:
    # Only object-level not-found codes count as a missing file. NoSuchBucket means
    # the artifacts bucket is misconfigured or missing -- a broken backend that must
    # surface (fail fast), not be masked as an absent object.
    code = err.response.get("Error", {}).get("Code", "")
    return code in {"404", "NoSuchKey", "NotFound"}


def _is_azure_container_not_found(err: ResourceNotFoundError) -> bool:
    # A missing container is a broken backend, not an absent blob; Azure tags the two
    # distinctly via the error code, so only the container case must fail fast.
    return getattr(err, "error_code", None) == "ContainerNotFound"


class _LocalFilesystemBackend:
    """Workspace stand-in: stores files under a local directory.

    Keeps `make validate-api` hermetic and free of cloud credentials. Nothing
    written here ships to production — Sandbox and Production services use the cloud backend.
    """

    def __init__(self) -> None:
        root = os.environ.get("ATLAS_LOCAL_STORAGE_DIR", "").strip()
        self._root = (
            Path(root)
            if root
            else Path(tempfile.gettempdir()) / "atlas-app-file-storage"
        )

    def _path(self, key: str) -> Path:
        return self._root / key

    def save(self, key: str, content: bytes, content_type: str | None) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def open(self, key: str) -> bytes:
        path = self._path(key)
        if not path.exists():
            raise FileNotFoundError(key)
        return path.read_bytes()

    def delete(self, key: str) -> None:
        # Missing files are a no-op so deletes stay idempotent.
        self._path(key).unlink(missing_ok=True)

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()


class _CloudStorageBackend:
    """Real object storage scoped to `apps/{APP_ID}/files/` in the artifacts bucket."""

    def __init__(self) -> None:
        self.provider = _get_provider()
        self._bucket = _get_required_env("ATLAS_ARTIFACTS_BUCKET")
        self._prefix = _OBJECT_PREFIX_TEMPLATE.format(
            app_id=_get_required_env("APP_ID")
        )
        self._gcs_client: storage.Client | None = None
        self._s3_client = None
        self._blob_service_client: BlobServiceClient | None = None

        if self.provider == "gcp":
            self._gcs_client = storage.Client()
        elif self.provider == "aws":
            region = _get_required_env("AWS_REGION")
            self._s3_client = boto3.client("s3", region_name=region)
        else:
            account_name = _get_required_env("AZURE_STORAGE_ACCOUNT_NAME")
            self._blob_service_client = BlobServiceClient(
                account_url=f"https://{account_name}.blob.core.windows.net",
                credential=build_azure_credential(),
            )

    def _object_key(self, key: str) -> str:
        return f"{self._prefix}{key}"

    def save(self, key: str, content: bytes, content_type: str | None) -> None:
        object_key = self._object_key(key)
        if self.provider == "gcp":
            if self._gcs_client is None:
                raise RuntimeError("GCS client not initialized")
            blob = self._gcs_client.bucket(self._bucket).blob(object_key)
            blob.upload_from_string(content, content_type=content_type)
            return
        if self.provider == "aws":
            if self._s3_client is None:
                raise RuntimeError("S3 client not initialized")
            extra = {"ContentType": content_type} if content_type else {}
            self._s3_client.put_object(
                Bucket=self._bucket, Key=object_key, Body=content, **extra
            )
            return
        if self._blob_service_client is None:
            raise RuntimeError("Azure Blob client not initialized")
        blob_client = self._blob_service_client.get_blob_client(
            container=self._bucket, blob=object_key
        )
        settings = ContentSettings(content_type=content_type) if content_type else None
        blob_client.upload_blob(content, overwrite=True, content_settings=settings)

    def open(self, key: str) -> bytes:
        object_key = self._object_key(key)
        if self.provider == "gcp":
            if self._gcs_client is None:
                raise RuntimeError("GCS client not initialized")
            # The runner holds object-scoped access (storage.objectAdmin) but not
            # storage.buckets.get, so a missing bucket cannot be probed or told apart
            # from a missing object here -- both surface as NotFound and are absence.
            # (AWS/Azure get that distinction for free from the operation's own error.)
            try:
                blob = self._gcs_client.bucket(self._bucket).blob(object_key)
                return blob.download_as_bytes()
            except GCSNotFound as err:
                raise FileNotFoundError(key) from err
        if self.provider == "aws":
            if self._s3_client is None:
                raise RuntimeError("S3 client not initialized")
            try:
                response = self._s3_client.get_object(
                    Bucket=self._bucket, Key=object_key
                )
            except ClientError as err:
                if _is_s3_not_found(err):
                    raise FileNotFoundError(key) from err
                raise
            return response["Body"].read()
        if self._blob_service_client is None:
            raise RuntimeError("Azure Blob client not initialized")
        blob_client = self._blob_service_client.get_blob_client(
            container=self._bucket, blob=object_key
        )
        try:
            data = blob_client.download_blob().readall()
        except ResourceNotFoundError as err:
            # A missing container is a broken backend; only a missing blob is absence.
            if _is_azure_container_not_found(err):
                raise
            raise FileNotFoundError(key) from err
        # readall() is typed str | bytes; objects are always stored as bytes.
        return data if isinstance(data, bytes) else data.encode("utf-8")

    def delete(self, key: str) -> None:
        object_key = self._object_key(key)
        if self.provider == "gcp":
            if self._gcs_client is None:
                raise RuntimeError("GCS client not initialized")
            try:
                self._gcs_client.bucket(self._bucket).blob(object_key).delete()
            except GCSNotFound:
                # Missing objects are a no-op so deletes stay idempotent. The runner
                # lacks storage.buckets.get, so a missing bucket can't be told apart
                # from a missing object; both are treated as absence.
                return
            return
        if self.provider == "aws":
            if self._s3_client is None:
                raise RuntimeError("S3 client not initialized")
            try:
                self._s3_client.delete_object(Bucket=self._bucket, Key=object_key)
            except ClientError as err:
                if _is_s3_not_found(err):
                    return
                raise
            return
        if self._blob_service_client is None:
            raise RuntimeError("Azure Blob client not initialized")
        blob_client = self._blob_service_client.get_blob_client(
            container=self._bucket, blob=object_key
        )
        try:
            blob_client.delete_blob()
        except ResourceNotFoundError as err:
            # Missing blobs are an idempotent no-op; a missing container must surface.
            if _is_azure_container_not_found(err):
                raise
            return

    def exists(self, key: str) -> bool:
        object_key = self._object_key(key)
        if self.provider == "gcp":
            if self._gcs_client is None:
                raise RuntimeError("GCS client not initialized")
            return self._gcs_client.bucket(self._bucket).blob(object_key).exists()
        if self.provider == "aws":
            if self._s3_client is None:
                raise RuntimeError("S3 client not initialized")
            try:
                self._s3_client.head_object(Bucket=self._bucket, Key=object_key)
                return True
            except ClientError as err:
                if _is_s3_not_found(err):
                    return False
                raise
        if self._blob_service_client is None:
            raise RuntimeError("Azure Blob client not initialized")
        blob_client = self._blob_service_client.get_blob_client(
            container=self._bucket, blob=object_key
        )
        try:
            blob_client.get_blob_properties()
            return True
        except ResourceNotFoundError as err:
            # A missing blob is absence; a missing container is a broken backend that
            # must surface, matching open_file/delete_file. The SDK's exists() swallows
            # ContainerNotFound, so probe properties (a blobs/read the runner already
            # holds) to read the error code. Unlike GCS, this needs no extra grant.
            if _is_azure_container_not_found(err):
                raise
            return False


_backend: _LocalFilesystemBackend | _CloudStorageBackend | None = None


def _get_backend() -> _LocalFilesystemBackend | _CloudStorageBackend:
    global _backend
    if _backend is None:
        _backend = (
            _LocalFilesystemBackend()
            if _is_workspace_runtime()
            else _CloudStorageBackend()
        )
    return _backend


def save_file(key: str, content: bytes, content_type: str | None = None) -> str:
    """Store file bytes under the app's scoped prefix; returns the file key.

    Persist the returned key (and your own metadata) in the database. `key` is a
    logical path such as `uploads/<uuid>/<filename>`.
    """
    normalized = _normalize_key(key)
    _get_backend().save(normalized, content, content_type)
    return normalized


def open_file(key: str) -> bytes:
    """Read file bytes by key. Raises FileNotFoundError if the key is unknown."""
    return _get_backend().open(_normalize_key(key))


def delete_file(key: str) -> None:
    """Delete a file by key. Missing keys are a no-op."""
    _get_backend().delete(_normalize_key(key))


def file_exists(key: str) -> bool:
    """Return whether a file exists for the given key."""
    return _get_backend().exists(_normalize_key(key))
