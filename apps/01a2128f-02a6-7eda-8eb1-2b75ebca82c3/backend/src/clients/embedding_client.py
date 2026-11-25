"""
Shared embedding client helpers for backend services.

This wrapper centralizes embedding provider selection:
- Workspace: always uses Vertex AI in the Atlas platform project.
- Sandbox and Production AWS apps: use Bedrock.
- Sandbox and Production GCP apps: use Vertex AI.
- Sandbox and Production Azure apps: use Azure Foundry.

For AWS and Azure cloud workspaces, Vertex embeddings are projected to
match the app embedding dimension set via APP_EMBEDDING_DIMENSION.
"""

import json
import os
from dataclasses import dataclass
from typing import Any, Literal

import boto3
from google import genai
from google.genai import types
from openai import AzureOpenAI

from .azure_credential import build_bearer_token_provider


def _get_embedding_dimension() -> int:
    raw = os.environ.get("APP_EMBEDDING_DIMENSION", "").strip()
    if not raw:
        raise RuntimeError("APP_EMBEDDING_DIMENSION is required")
    return int(raw)


EMBEDDING_DIMENSION = _get_embedding_dimension()


@dataclass(frozen=True)
class EmbeddingRuntimeConfig:
    provider: Literal["azure", "bedrock", "vertex"]
    model: str
    region: str | None = None
    project_id: str | None = None
    location: str | None = None
    endpoint: str | None = None
    output_dimensionality: int | None = None


def _get_required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _is_workspace_runtime() -> bool:
    return os.environ.get("IS_WORKSPACE", "").strip().lower() == "true"


def _get_bedrock_embedding_model_id() -> str:
    return _get_required_env("APP_BEDROCK_EMBEDDING_MODEL")


def _build_vertex_runtime_config(
    *, output_dimensionality: int | None, project_env_var: str
) -> EmbeddingRuntimeConfig:
    project_id = _get_required_env(project_env_var)
    # Temporary: Vertex AI Gemini embedding models are currently only available
    # in us-central1. Remove this override and use APP_VERTEX_AI_LOCATION once
    # Vertex AI expands Gemini embedding availability.
    # location = _get_required_env("APP_VERTEX_AI_LOCATION")
    location = "us-central1"
    model = _get_required_env("APP_VERTEX_AI_EMBEDDING_MODEL")
    return EmbeddingRuntimeConfig(
        provider="vertex",
        model=model,
        project_id=project_id,
        location=location,
        output_dimensionality=output_dimensionality,
    )


def _build_bedrock_runtime_config() -> EmbeddingRuntimeConfig:
    # Temporary: Amazon Nova Multimodal Embeddings (amazon.nova-2-multimodal-embeddings-v1:0)
    # is currently only available in us-east-1. Remove this override and use
    # APP_BEDROCK_REGION once AWS expands Nova embedding availability.
    # region = _get_required_env("APP_BEDROCK_REGION")
    region = "us-east-1"
    model = _get_bedrock_embedding_model_id()
    return EmbeddingRuntimeConfig(
        provider="bedrock",
        model=model,
        region=region,
    )


def _build_azure_runtime_config() -> EmbeddingRuntimeConfig:
    endpoint = _get_required_env("APP_AZURE_FOUNDRY_OPENAI_BASE_URL")
    model = _get_required_env("APP_AZURE_FOUNDRY_EMBEDDING_MODEL")
    return EmbeddingRuntimeConfig(
        provider="azure",
        model=model,
        endpoint=endpoint,
    )


def get_embedding_runtime_config() -> EmbeddingRuntimeConfig:
    cloud_provider = _get_required_env("CLOUD_PROVIDER").lower()

    if _is_workspace_runtime():
        output_dimensionality: int | None = None
        if cloud_provider in {"aws", "azure"}:
            output_dimensionality = EMBEDDING_DIMENSION
        elif cloud_provider != "gcp":
            raise RuntimeError(f"Unsupported CLOUD_PROVIDER: {cloud_provider}")
        return _build_vertex_runtime_config(
            output_dimensionality=output_dimensionality,
            project_env_var="WORKSPACE_VERTEX_AI_PROJECT",
        )

    if cloud_provider == "aws":
        return _build_bedrock_runtime_config()
    if cloud_provider == "azure":
        return _build_azure_runtime_config()
    if cloud_provider == "gcp":
        return _build_vertex_runtime_config(
            output_dimensionality=None,
            project_env_var="APP_VERTEX_AI_PROJECT",
        )
    raise RuntimeError(f"Unsupported CLOUD_PROVIDER: {cloud_provider}")


def _embed_with_vertex(
    config: EmbeddingRuntimeConfig,
    *,
    text: str,
    task_type: Literal["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"],
) -> list[float]:
    client = genai.Client(
        vertexai=True,
        project=config.project_id,
        location=config.location,
    )
    embed_config: dict[str, Any] = {"task_type": task_type}
    if config.output_dimensionality is not None:
        embed_config["output_dimensionality"] = config.output_dimensionality

    result = client.models.embed_content(
        model=config.model,
        contents=[text],
        config=types.EmbedContentConfig(**embed_config),
    )
    if not result.embeddings:
        raise RuntimeError("Vertex AI embedding response is missing embeddings")

    vector = result.embeddings[0].values
    if not vector:
        raise RuntimeError("Vertex AI embedding response is missing embedding values")

    return [float(value) for value in vector]


def _embed_with_bedrock(
    config: EmbeddingRuntimeConfig,
    *,
    text: str,
    input_type: Literal["search_document", "search_query"],
) -> list[float]:
    client = boto3.client("bedrock-runtime", region_name=config.region)

    embedding_purpose = (
        "GENERIC_INDEX" if input_type == "search_document" else "TEXT_RETRIEVAL"
    )
    payload = {
        "taskType": "SINGLE_EMBEDDING",
        "singleEmbeddingParams": {
            "embeddingPurpose": embedding_purpose,
            "embeddingDimension": EMBEDDING_DIMENSION,
            "text": {
                "truncationMode": "END",
                "value": text,
            },
        },
    }
    response = client.invoke_model(
        modelId=config.model,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(payload),
    )

    result = json.loads(response["body"].read())
    embeddings = result.get("embeddings")
    if not isinstance(embeddings, list) or len(embeddings) != 1:
        raise RuntimeError("Bedrock embedding response is missing embeddings")
    embedding_payload = embeddings[0]
    if not isinstance(embedding_payload, dict):
        raise TypeError("Bedrock embedding response is invalid")
    vector = embedding_payload.get("embedding")
    if not isinstance(vector, list) or not vector:
        raise RuntimeError("Bedrock embedding response vector is invalid")

    return [float(value) for value in vector]


def _embed_with_azure(
    config: EmbeddingRuntimeConfig,
    *,
    text: str,
) -> list[float]:
    endpoint = config.endpoint
    if endpoint is None:
        raise RuntimeError("Azure Foundry embedding endpoint is required")

    # text-embedding-3-large is deployed on Foundry under the OpenAI API
    # surface, not the unified MaaS `/models` endpoint. Foundry's MaaS path
    # rewrites OpenAI-deployed embedding calls to a legacy `/v1/engines/...`
    # URL that returns 200 with an empty body. Use the OpenAI SDK so the
    # request lands on `/openai/deployments/{name}/embeddings` directly.
    client: Any = AzureOpenAI(
        azure_endpoint=endpoint,
        api_version="2024-08-01-preview",
        azure_ad_token_provider=build_bearer_token_provider(
            "https://ai.azure.com/.default"
        ),
    )
    result = client.embeddings.create(
        input=text,
        model=config.model,
        dimensions=EMBEDDING_DIMENSION,
    )
    if not result.data:
        raise RuntimeError("Azure Foundry embedding response is missing embeddings")

    vector = result.data[0].embedding
    if not vector:
        raise RuntimeError(
            "Azure Foundry embedding response is missing embedding values"
        )

    return [float(value) for value in vector]


def embed_document(text: str) -> list[float]:
    normalized_text = text.strip()
    if not normalized_text:
        raise RuntimeError("embedding text is required")

    runtime = get_embedding_runtime_config()
    if runtime.provider == "vertex":
        return _embed_with_vertex(
            runtime,
            text=normalized_text,
            task_type="RETRIEVAL_DOCUMENT",
        )
    if runtime.provider == "azure":
        return _embed_with_azure(runtime, text=normalized_text)
    return _embed_with_bedrock(
        runtime,
        text=normalized_text,
        input_type="search_document",
    )


def embed_query(text: str) -> list[float]:
    normalized_text = text.strip()
    if not normalized_text:
        raise RuntimeError("embedding text is required")

    runtime = get_embedding_runtime_config()
    if runtime.provider == "vertex":
        return _embed_with_vertex(
            runtime,
            text=normalized_text,
            task_type="RETRIEVAL_QUERY",
        )
    if runtime.provider == "azure":
        return _embed_with_azure(runtime, text=normalized_text)
    return _embed_with_bedrock(
        runtime,
        text=normalized_text,
        input_type="search_query",
    )
