"""
Shared Anthropic client helpers for backend services.

This wrapper centralizes Claude provider selection:
- Workspace: uses Atlas-managed Vertex AI Gemini and projects the text response
  onto the Anthropic response surface.
- Sandbox and Production AWS apps: use Bedrock.
- Sandbox and Production GCP apps: use Vertex AI.

Defaults applied by create_anthropic_message for cloud Claude providers:
- thinking: adaptive — the model dynamically decides when and how much to
  reason per request. Replaces the deprecated budget_tokens approach on
  Claude 4.6 models. Interleaved thinking is automatically enabled,
  allowing the model to reason between tool calls. Workspace generation maps
  output_config effort to Gemini thinking levels instead.
- max_tokens: 16000 — includes both thinking and response tokens. Increase
  if responses return stop_reason "max_tokens".

Constraints when thinking is enabled:
- Do not set temperature, top_k, or top_p — the API rejects requests
  that include them.
- Do not use forced tool_choice (type: "tool" or "any") — use type
  "auto" and instruct the model via system to always call the tool.
- To control thinking depth, pass output_config={"effort": level}.
  Default is "high". Use "low" or "medium" for faster, cheaper
  responses. "max" is Opus 4.6 only.

Response parsing:
- With thinking enabled, response.content may contain thinking blocks
  before the text block. Use get_text_content() to extract the text
  response safely instead of response.content[0].text.
"""

import os
from dataclasses import dataclass
from typing import Any

from anthropic import AnthropicBedrock, AnthropicVertex

from .gemini_client import (
    GeminiRuntimeConfig,
    generate_gemini_message,
    get_gemini_runtime_config,
)


@dataclass(frozen=True)
class AnthropicRuntimeConfig:
    client: AnthropicBedrock | AnthropicVertex
    model: str


def _get_required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _is_workspace_runtime() -> bool:
    return os.environ.get("IS_WORKSPACE", "").strip().lower() == "true"


def _build_vertex_runtime_config() -> AnthropicRuntimeConfig:
    project_id = _get_required_env("APP_VERTEX_AI_PROJECT")
    location = _get_required_env("APP_VERTEX_AI_LOCATION")
    model = _get_required_env("APP_VERTEX_AI_MODEL")
    client = AnthropicVertex(project_id=project_id, region=location)
    return AnthropicRuntimeConfig(client=client, model=model)


def _build_workspace_runtime_config() -> GeminiRuntimeConfig:
    return get_gemini_runtime_config()


def _build_bedrock_runtime_config() -> AnthropicRuntimeConfig:
    region = _get_required_env("APP_BEDROCK_REGION")
    model = _get_required_env("APP_BEDROCK_MODEL_ID")
    client = AnthropicBedrock(aws_region=region)
    return AnthropicRuntimeConfig(client=client, model=model)


def get_anthropic_runtime_config() -> AnthropicRuntimeConfig | GeminiRuntimeConfig:
    if _is_workspace_runtime():
        return _build_workspace_runtime_config()

    cloud_provider = _get_required_env("CLOUD_PROVIDER").lower()
    if cloud_provider == "aws":
        return _build_bedrock_runtime_config()
    if cloud_provider == "gcp":
        return _build_vertex_runtime_config()
    raise RuntimeError(f"Unsupported CLOUD_PROVIDER: {cloud_provider}")


def get_anthropic_client() -> Any:
    return get_anthropic_runtime_config().client


def get_anthropic_model() -> str:
    return get_anthropic_runtime_config().model


def get_text_content(response: Any) -> str:
    """Extract text from a response, skipping thinking blocks."""
    for block in response.content:
        if block.type == "text":
            return block.text
    return ""


def _deployed_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    translated: list[dict[str, Any]] = []
    for message in messages:
        content = message.get("content")
        state_blocks = (
            [
                block
                for block in content
                if isinstance(block, dict) and block.get("type") == "provider_state"
            ]
            if isinstance(content, list)
            else []
        )
        if not state_blocks:
            translated.append(message)
            continue
        if not isinstance(content, list) or len(content) != 1:
            raise RuntimeError("generation provider state must be replayed unchanged")
        block = state_blocks[0]
        if block.get("provider") != "anthropic":
            raise RuntimeError("generation history belongs to a different AI provider")
        state = block.get("state")
        if not isinstance(state, dict):
            raise TypeError("Anthropic provider state must be an object")
        raw_content = state.get("content")
        if not isinstance(raw_content, list):
            raise TypeError("Anthropic provider state is missing content")
        translated.append({"role": "assistant", "content": raw_content})
    return translated


def create_anthropic_message(
    *,
    messages: list[dict[str, Any]],
    max_tokens: int = 16000,
    **kwargs: Any,
) -> Any:
    if _is_workspace_runtime():
        tools = kwargs.pop("tools", None)
        if tools is not None and not isinstance(tools, list):
            raise RuntimeError("workspace Anthropic tools must be a list")
        tool_choice = kwargs.pop("tool_choice", None)
        if tool_choice is not None and (
            not isinstance(tool_choice, dict) or tool_choice.get("type") != "auto"
        ):
            raise RuntimeError(
                "The build workspace supports only automatic Anthropic tool choice"
            )
        system = kwargs.pop("system", None)
        if system is not None and not isinstance(system, str):
            raise RuntimeError("workspace Anthropic system instructions must be text")
        stop_sequences = kwargs.pop("stop_sequences", None)
        output_config = kwargs.pop("output_config", None)
        effort = None
        if isinstance(output_config, dict):
            effort_value = output_config.get("effort")
            if effort_value is not None and not isinstance(effort_value, str):
                raise RuntimeError("workspace Anthropic reasoning effort must be text")
            effort = effort_value
        elif output_config is not None:
            raise RuntimeError("workspace Anthropic output_config must be an object")
        remaining = [key for key, value in kwargs.items() if value is not None]
        if remaining:
            raise RuntimeError(
                "These Anthropic options are not supported in the build workspace, "
                "where generation runs on Vertex AI Gemini: " + ", ".join(remaining)
            )
        response = generate_gemini_message(
            messages=messages,
            system=system,
            max_tokens=max_tokens,
            stop_sequences=stop_sequences,
            effort=effort,
            tools=tools,
        )
        content: list[_WorkspaceTextBlock | _WorkspaceToolUseBlock] = []
        if response.text:
            content.append(_WorkspaceTextBlock(type="text", text=response.text))
        content.extend(
            _WorkspaceToolUseBlock(
                type="tool_use",
                id=call.id,
                name=call.name,
                input=call.arguments,
                provider_part=call.provider_part,
            )
            for call in response.function_calls
        )
        return _WorkspaceAnthropicMessage(
            content=content,
            model=response.model,
            stop_reason=_workspace_stop_reason(
                response.finish_reason,
                has_tool_calls=bool(response.function_calls),
            ),
            assistant_message=response.assistant_message,
        )

    runtime = get_anthropic_runtime_config()
    if isinstance(runtime, GeminiRuntimeConfig):
        raise TypeError("workspace generation must use the Gemini adapter")
    kwargs["thinking"] = {"type": "adaptive"}
    return runtime.client.messages.create(  # ty: ignore[no-matching-overload]
        model=runtime.model,
        max_tokens=max_tokens,
        messages=_deployed_messages(messages),
        **kwargs,
    )


@dataclass(frozen=True)
class _WorkspaceTextBlock:
    type: str
    text: str


@dataclass(frozen=True)
class _WorkspaceToolUseBlock:
    type: str
    id: str
    name: str
    input: dict[str, Any]
    provider_part: dict[str, Any] | None


@dataclass(frozen=True)
class _WorkspaceAnthropicMessage:
    content: list[_WorkspaceTextBlock | _WorkspaceToolUseBlock]
    model: str
    assistant_message: dict[str, Any] | None
    stop_reason: str = "end_turn"


def _workspace_stop_reason(finish_reason: str, *, has_tool_calls: bool) -> str:
    normalized = finish_reason.upper()
    if normalized == "MAX_TOKENS":
        return "max_tokens"
    if normalized in {
        "SAFETY",
        "BLOCKLIST",
        "PROHIBITED_CONTENT",
        "SPII",
        "IMAGE_SAFETY",
        "RECITATION",
        "PROMPT_BLOCKED",
    }:
        return "refusal"
    if normalized == "STOP":
        return "tool_use" if has_tool_calls else "end_turn"
    raise RuntimeError(f"Gemini generation stopped unexpectedly: {finish_reason}")
