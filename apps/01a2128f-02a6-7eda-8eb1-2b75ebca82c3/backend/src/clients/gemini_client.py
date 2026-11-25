"""Vertex AI Gemini adapter for app generation.

The target app provider remains Gemini when the app runs on GCP. In a
build workspace, every target-cloud adapter delegates generation here and this
module uses the Atlas-managed workspace model instead.
"""

from __future__ import annotations

import base64
import binascii
import os
from dataclasses import dataclass
from typing import Any, cast

from google import genai
from google.genai import types


@dataclass(frozen=True)
class GeminiRuntimeConfig:
    client: genai.Client
    model: str


@dataclass(frozen=True)
class GeminiFunctionCall:
    id: str
    name: str
    arguments: dict[str, Any]
    provider_part: dict[str, Any] | None = None


@dataclass(frozen=True)
class GeminiResponse:
    text: str
    model: str
    function_calls: list[GeminiFunctionCall]
    finish_reason: str
    assistant_message: dict[str, Any] | None


def _get_required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _is_workspace_runtime() -> bool:
    return os.environ.get("IS_WORKSPACE", "").strip().lower() == "true"


def get_gemini_runtime_config() -> GeminiRuntimeConfig:
    if _is_workspace_runtime():
        project_id = _get_required_env("WORKSPACE_VERTEX_AI_PROJECT")
        location = _get_required_env("WORKSPACE_VERTEX_AI_LOCATION")
        model = _get_required_env("WORKSPACE_VERTEX_AI_MODEL")
    else:
        cloud_provider = _get_required_env("CLOUD_PROVIDER").lower()
        if cloud_provider != "gcp":
            raise RuntimeError(
                f"Unsupported CLOUD_PROVIDER for Gemini: {cloud_provider}"
            )
        project_id = _get_required_env("APP_VERTEX_AI_PROJECT")
        location = _get_required_env("APP_VERTEX_AI_LOCATION")
        model = _get_required_env("APP_VERTEX_AI_MODEL")
    return GeminiRuntimeConfig(
        client=genai.Client(vertexai=True, project=project_id, location=location),
        model=model,
    )


def _decode_base64(data: Any) -> bytes:
    if not isinstance(data, str) or not data:
        raise RuntimeError("Gemini document block is missing base64 data")
    try:
        return base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise RuntimeError("Gemini document block has invalid base64 data") from exc


def _tool_result_response(content: Any) -> dict[str, Any]:
    if isinstance(content, dict):
        return content
    if isinstance(content, list):
        if content and all(
            isinstance(part, dict) and part.get("type") == "text" for part in content
        ):
            return {"result": "\n".join(part.get("text", "") for part in content)}
        return {"result": content}
    return {"result": str(content)}


def _normalize_projected_block(block: Any) -> dict[str, Any]:
    if isinstance(block, dict):
        return block
    block_type = getattr(block, "type", None)
    if block_type == "text":
        return {"type": "text", "text": getattr(block, "text", None)}
    if block_type == "tool_use":
        return {
            "type": "tool_use",
            "id": getattr(block, "id", None),
            "name": getattr(block, "name", None),
            "input": getattr(block, "input", None),
            "provider_part": getattr(block, "provider_part", None),
        }
    raise RuntimeError("Gemini message content blocks must be objects")


def _provider_content(
    content: Any, tool_names: dict[str, str], function_call_ids: set[str]
) -> dict[str, Any] | None:
    if not isinstance(content, list):
        return None
    state_blocks = [
        block
        for block in content
        if isinstance(block, dict) and block.get("type") == "provider_state"
    ]
    if not state_blocks:
        return None
    if len(content) != 1:
        raise RuntimeError("generation provider state must be replayed unchanged")
    block = state_blocks[0]
    if block.get("provider") != "gemini":
        raise RuntimeError("generation history belongs to a different AI provider")
    state = block.get("state")
    if not isinstance(state, dict):
        raise TypeError("Gemini provider state must be an object")
    raw_content = state.get("content")
    if not isinstance(raw_content, dict):
        raise TypeError("Gemini provider state is missing content")
    raw_tool_names = state.get("tool_names")
    if not isinstance(raw_tool_names, dict) or not all(
        isinstance(tool_id, str) and isinstance(name, str)
        for tool_id, name in raw_tool_names.items()
    ):
        raise RuntimeError("Gemini provider state has invalid tool names")
    tool_names.update(raw_tool_names)
    raw_parts = raw_content.get("parts")
    if isinstance(raw_parts, list):
        for part in raw_parts:
            function_call = (
                part.get("function_call") if isinstance(part, dict) else None
            )
            call_id = (
                function_call.get("id") if isinstance(function_call, dict) else None
            )
            if isinstance(call_id, str) and call_id:
                function_call_ids.add(call_id)
    return raw_content


def _content_part(
    block: Any, tool_names: dict[str, str], function_call_ids: set[str]
) -> dict[str, Any]:
    normalized = _normalize_projected_block(block)
    block_type = normalized.get("type")
    if block_type == "text":
        text = normalized.get("text")
        if not isinstance(text, str):
            raise RuntimeError("Gemini text block is missing text")
        return {"text": text}
    if block_type in ("image", "document"):
        source = normalized.get("source")
        if not isinstance(source, dict) or source.get("type") != "base64":
            raise RuntimeError("Gemini media blocks must use inline base64 data")
        media_type = source.get("media_type")
        if not isinstance(media_type, str) or not media_type:
            raise RuntimeError("Gemini media block is missing its media type")
        return {
            "inline_data": {
                "mime_type": media_type,
                "data": _decode_base64(source.get("data")),
            }
        }
    if block_type == "tool_use":
        tool_id = normalized.get("id")
        name = normalized.get("name")
        arguments = normalized.get("input")
        if not isinstance(tool_id, str) or not tool_id:
            raise RuntimeError("Gemini tool-use block is missing its id")
        if not isinstance(name, str) or not name:
            raise RuntimeError("Gemini tool-use block is missing its name")
        if not isinstance(arguments, dict):
            raise RuntimeError("Gemini tool-use input must be an object")
        tool_names[tool_id] = name
        provider_part = normalized.get("provider_part")
        if provider_part is not None:
            if not isinstance(provider_part, dict):
                raise RuntimeError("Gemini tool-use provider part must be an object")
            provider_function_call = provider_part.get("function_call")
            if not isinstance(provider_function_call, dict):
                raise RuntimeError(
                    "Gemini tool-use provider part is missing its function call"
                )
            if (
                provider_function_call.get("name") != name
                or provider_function_call.get("args", {}) != arguments
            ):
                raise RuntimeError(
                    "Gemini tool-use provider part does not match the projected call"
                )
            provider_call_id = provider_function_call.get("id")
            if provider_call_id is not None:
                if provider_call_id != tool_id:
                    raise RuntimeError(
                        "Gemini tool-use provider part has a mismatched call id"
                    )
                function_call_ids.add(tool_id)
            return provider_part
        return {"function_call": {"name": name, "args": arguments}}
    if block_type == "tool_result":
        tool_id = normalized.get("tool_use_id")
        if not isinstance(tool_id, str) or tool_id not in tool_names:
            raise RuntimeError("Gemini tool result does not match a prior tool use")
        function_response = {
            "name": tool_names[tool_id],
            "response": _tool_result_response(normalized.get("content", "")),
        }
        if tool_id in function_call_ids:
            function_response["id"] = tool_id
        return {"function_response": function_response}
    raise RuntimeError(f"unsupported Gemini content block type: {block_type}")


def _contents(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    contents: list[dict[str, Any]] = []
    tool_names: dict[str, str] = {}
    function_call_ids: set[str] = set()
    for message in messages:
        role = message.get("role")
        if role == "assistant":
            role = "model"
        if role not in ("user", "model"):
            raise RuntimeError(f"unsupported Gemini message role: {role}")
        content = message.get("content")
        provider_content = _provider_content(content, tool_names, function_call_ids)
        if provider_content is not None:
            contents.append(provider_content)
            continue
        if isinstance(content, str):
            parts = [{"text": content}]
        elif isinstance(content, list):
            parts = [
                _content_part(block, tool_names, function_call_ids) for block in content
            ]
        else:
            raise TypeError("Gemini message content must be text or blocks")
        contents.append({"role": role, "parts": parts})
    return contents


def _tools(tools: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
    if not tools:
        return None
    declarations: list[dict[str, Any]] = []
    for tool in tools:
        name = tool.get("name")
        schema = tool.get("input_schema")
        if not isinstance(name, str) or not name:
            raise RuntimeError("Gemini tools require a name")
        if not isinstance(schema, dict):
            raise TypeError(f"Gemini tool {name} requires input_schema")
        declaration: dict[str, Any] = {
            "name": name,
            "parameters_json_schema": schema,
        }
        description = tool.get("description")
        if isinstance(description, str) and description:
            declaration["description"] = description
        declarations.append(declaration)
    return [{"function_declarations": declarations}]


def _serialized_content(content: Any) -> dict[str, Any]:
    serialized = content.model_dump(mode="json", exclude_none=True)
    if not isinstance(serialized, dict):
        raise TypeError("Gemini response content must serialize to an object")
    return serialized


def _function_calls(
    response: Any, serialized_content: dict[str, Any]
) -> list[GeminiFunctionCall]:
    raw_calls = response.function_calls or []
    raw_parts = serialized_content.get("parts")
    if not isinstance(raw_parts, list):
        raise TypeError("Gemini response content is missing parts")
    provider_parts = [
        part
        for part in raw_parts
        if isinstance(part, dict) and isinstance(part.get("function_call"), dict)
    ]
    if len(provider_parts) != len(raw_calls):
        raise RuntimeError("Gemini response function calls do not match its content")
    calls: list[GeminiFunctionCall] = []
    for index, (call, provider_part) in enumerate(
        zip(raw_calls, provider_parts, strict=True), start=1
    ):
        if not call.name:
            raise RuntimeError("Gemini returned a function call without a name")
        call_id = getattr(call, "id", None)
        if not isinstance(call_id, str) or not call_id:
            call_id = f"gemini_tool_{index}"
        calls.append(
            GeminiFunctionCall(
                id=call_id,
                name=call.name,
                arguments=dict(call.args or {}),
                provider_part=provider_part,
            )
        )
    return calls


def _assistant_message(
    serialized_content: dict[str, Any], calls: list[GeminiFunctionCall]
) -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": [
            {
                "type": "provider_state",
                "provider": "gemini",
                "state": {
                    "content": serialized_content,
                    "tool_names": {call.id: call.name for call in calls},
                },
            }
        ],
    }


def _finish_reason(response: Any) -> str:
    candidates = getattr(response, "candidates", None)
    if candidates:
        reason = getattr(candidates[0], "finish_reason", None)
    else:
        prompt_feedback = getattr(response, "prompt_feedback", None)
        reason = getattr(prompt_feedback, "block_reason", None)
        if reason is None:
            raise RuntimeError("Gemini response is missing candidates")
    if reason is None:
        raise RuntimeError("Gemini response is missing a finish reason")
    name = getattr(reason, "name", None)
    if isinstance(name, str) and name:
        normalized = name.upper()
    else:
        value = getattr(reason, "value", reason)
        normalized = str(value).rsplit(".", maxsplit=1)[-1].upper()
    if not candidates:
        if normalized == "BLOCKED_REASON_UNSPECIFIED":
            raise RuntimeError("Gemini prompt block is missing a reason")
        return "PROMPT_BLOCKED"
    return normalized


def generate_gemini_message(
    *,
    messages: list[dict[str, Any]],
    system: str | None = None,
    max_tokens: int = 16000,
    stop_sequences: list[str] | None = None,
    effort: str | None = None,
    tools: list[dict[str, Any]] | None = None,
) -> GeminiResponse:
    runtime = get_gemini_runtime_config()
    config: types.GenerateContentConfigDict = {"max_output_tokens": max_tokens}
    if system:
        config["system_instruction"] = system
    if stop_sequences:
        config["stop_sequences"] = stop_sequences
    if effort:
        if effort not in ("minimal", "low", "medium", "high"):
            raise RuntimeError(
                "Gemini reasoning effort must be minimal, low, medium, or high"
            )
        config["thinking_config"] = {
            "thinking_level": types.ThinkingLevel(effort.upper())
        }
    translated_tools = _tools(tools)
    if translated_tools:
        config["tools"] = cast(Any, translated_tools)

    # The SDK types contents as a union of its TypedDicts; the builder carries
    # stored provider parts as plain dicts, so it is cast at the boundary like
    # the tool declarations above.
    response = runtime.client.models.generate_content(
        model=runtime.model,
        contents=cast(Any, _contents(messages)),
        config=config,
    )
    finish_reason = _finish_reason(response)
    candidates = getattr(response, "candidates", None)
    content = getattr(candidates[0], "content", None) if candidates else None
    if content is None:
        if finish_reason not in {
            "MAX_TOKENS",
            "SAFETY",
            "BLOCKLIST",
            "PROHIBITED_CONTENT",
            "SPII",
            "IMAGE_SAFETY",
            "RECITATION",
            "PROMPT_BLOCKED",
        }:
            raise RuntimeError("Gemini response is missing candidate content")
        text = ""
        function_calls: list[GeminiFunctionCall] = []
        assistant_message = None
    else:
        text = response.text or ""
        serialized_content = _serialized_content(content)
        function_calls = _function_calls(response, serialized_content)
        assistant_message = _assistant_message(serialized_content, function_calls)
    return GeminiResponse(
        text=text,
        model=runtime.model,
        function_calls=function_calls,
        finish_reason=finish_reason,
        assistant_message=assistant_message,
    )


def generate_gemini_text(
    *,
    messages: list[dict[str, Any]],
    system: str | None = None,
    max_tokens: int = 16000,
    stop_sequences: list[str] | None = None,
    effort: str | None = None,
) -> tuple[str, str]:
    response = generate_gemini_message(
        messages=messages,
        system=system,
        max_tokens=max_tokens,
        stop_sequences=stop_sequences,
        effort=effort,
    )
    return response.text, response.model
