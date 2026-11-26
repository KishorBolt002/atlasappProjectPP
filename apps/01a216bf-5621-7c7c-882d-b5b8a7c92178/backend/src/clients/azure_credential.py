import os
import urllib.parse
import urllib.request

from azure.identity import (
    ClientAssertionCredential,
    ManagedIdentityCredential,
    WorkloadIdentityCredential,
    get_bearer_token_provider,
)

_AZURE_TOKEN_EXCHANGE_AUDIENCE = "api://AzureADTokenExchange"


def _get_required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _metadata_id_token(audience: str) -> str:
    query = urllib.parse.urlencode({"audience": audience, "format": "full"})
    # nosemgrep: env-read-with-literal-default - unset means the GCE metadata server
    metadata_host = os.environ.get("GCE_METADATA_HOST", "metadata.google.internal")
    req = urllib.request.Request(
        f"http://{metadata_host}/computeMetadata/v1/instance/service-accounts/default/identity"
        f"?{query}",
        headers={"Metadata-Flavor": "Google"},
    )
    try:
        # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected -- request goes to the GCE metadata host, a fixed address or the platform-set GCE_METADATA_HOST
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                raise RuntimeError(f"metadata server returned {resp.status}")
            token = resp.read().decode("utf-8").strip()
    except Exception as exc:
        raise RuntimeError(f"failed to fetch metadata token: {exc}") from exc

    if not token:
        raise RuntimeError("metadata token response was empty")
    return token


def _has_azure_managed_identity_endpoint() -> bool:
    return bool(
        os.environ.get("IDENTITY_ENDPOINT", "").strip()
        and os.environ.get("IDENTITY_HEADER", "").strip()
    )


def build_azure_credential():
    tenant_id = _get_required_env("AZURE_TENANT_ID")
    client_id = _get_required_env("AZURE_CLIENT_ID")

    token_file = os.environ.get("AZURE_FEDERATED_TOKEN_FILE", "").strip()
    if token_file:
        return WorkloadIdentityCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            token_file_path=token_file,
        )

    if _has_azure_managed_identity_endpoint():
        return ManagedIdentityCredential(client_id=client_id)

    return ClientAssertionCredential(
        tenant_id,
        client_id,
        lambda: _metadata_id_token(_AZURE_TOKEN_EXCHANGE_AUDIENCE),
    )


def build_bearer_token_provider(scope: str):
    return get_bearer_token_provider(build_azure_credential(), scope)
