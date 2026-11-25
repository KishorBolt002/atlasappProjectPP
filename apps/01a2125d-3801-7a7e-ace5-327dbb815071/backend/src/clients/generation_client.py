"""Provider-neutral generation interface for app code.

App code imports this module regardless of its target cloud. The selected target
provider chooses the cloud adapter, and each adapter switches to Atlas-managed
Gemini while the app is running in a build workspace.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from jsonschema import exceptions as jsonschema_exceptions
from jsonschema.validators import validator_for

from .anthropic_client import create_anthropic_message
from .gemini_client import generate_gemini_message
from .openai_client import create_openai_generation


@dataclass(frozen=True)
class GenerationToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class GenerationResponse:
    text: str
    model: str
    stop_reason: str
    tool_calls: list[GenerationToolCall]
    assistant_message: dict[str, Any] | None


def _get_required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _adapter_block(block: Any) -> dict[str, Any]:
    if not isinstance(block, dict):
        raise TypeError("generation content blocks must be objects")
    block_type = block.get("type")
    if block_type == "text":
        text = block.get("text")
        if not isinstance(text, str):
            raise RuntimeError("generation text block is missing text")
        return {"type": "text", "text": text}
    if block_type == "file":
        media_type = block.get("media_type")
        data = block.get("data")
        if not isinstance(media_type, str) or not media_type:
            raise RuntimeError("generation file block is missing its media type")
        if not isinstance(data, str) or not data:
            raise RuntimeError("generation file block is missing base64 data")
        return {
            "type": "image" if media_type.startswith("image/") else "document",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": data,
            },
        }
    if block_type == "tool_call":
        tool_id = block.get("id")
        name = block.get("name")
        arguments = block.get("arguments")
        if not isinstance(tool_id, str) or not tool_id:
            raise RuntimeError("generation tool call is missing its id")
        if not isinstance(name, str) or not name:
            raise RuntimeError("generation tool call is missing its name")
        if not isinstance(arguments, dict):
            raise RuntimeError("generation tool-call arguments must be an object")
        return {
            "type": "tool_use",
            "id": tool_id,
            "name": name,
            "input": arguments,
        }
    if block_type == "tool_result":
        tool_id = block.get("tool_call_id")
        if not isinstance(tool_id, str) or not tool_id:
            raise RuntimeError("generation tool result is missing its tool-call id")
        return {
            "type": "tool_result",
            "tool_use_id": tool_id,
            "content": block.get("content", ""),
        }
    if block_type == "provider_state":
        provider = block.get("provider")
        state = block.get("state")
        if not isinstance(provider, str) or not provider:
            raise RuntimeError("generation provider state is missing its provider")
        if not isinstance(state, dict):
            raise RuntimeError("generation provider state must be an object")
        return {
            "type": "provider_state",
            "provider": provider,
            "state": state,
        }
    raise RuntimeError(f"unsupported generation content block type: {block_type}")


def _adapter_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    translated: list[dict[str, Any]] = []
    for message in messages:
        role = message.get("role")
        if role not in ("user", "assistant"):
            raise RuntimeError(f"unsupported generation message role: {role}")
        content = message.get("content")
        if isinstance(content, str):
            translated_content: str | list[dict[str, Any]] = content
        elif isinstance(content, list):
            translated_content = [_adapter_block(block) for block in content]
        else:
            raise TypeError("generation message content must be text or blocks")
        translated.append({"role": role, "content": translated_content})
    return translated


def _anthropic_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    translated: list[dict[str, Any]] = []
    for message in messages:
        content = message["content"]
        if not isinstance(content, list):
            translated.append(message)
            continue
        blocks: list[dict[str, Any]] = []
        for block in content:
            result = block.get("content")
            if block.get("type") == "tool_result" and not isinstance(result, str):
                blocks.append({**block, "content": json.dumps(result)})
            else:
                blocks.append(block)
        translated.append({**message, "content": blocks})
    return translated


def _schema_instruction(response_schema: dict[str, Any] | None) -> str | None:
    if response_schema is None:
        return None
    return (
        "Respond with only one JSON value that conforms to this JSON Schema, "
        "without markdown fences or surrounding prose: "
        + json.dumps(response_schema, separators=(",", ":"))
    )


def _combine_system(
    system: str | None, response_schema: dict[str, Any] | None
) -> str | None:
    parts = [part for part in (system, _schema_instruction(response_schema)) if part]
    return "\n\n".join(parts) or None


def _schema_validator(response_schema: dict[str, Any] | None) -> Any | None:
    if response_schema is None:
        return None
    validator_class = validator_for(response_schema)
    try:
        validator_class.check_schema(response_schema)
    except jsonschema_exceptions.SchemaError as exc:
        raise RuntimeError("response_schema is not a valid JSON Schema") from exc
    return validator_class(response_schema)


def _reject_non_json_constant(value: str) -> None:
    raise ValueError(f"invalid JSON constant: {value}")


def _validate_structured_response(
    response: GenerationResponse, validator: Any | None
) -> GenerationResponse:
    if validator is None or response.stop_reason != "end_turn":
        return response
    try:
        value = json.loads(response.text, parse_constant=_reject_non_json_constant)
    except ValueError as exc:
        raise RuntimeError("generation response is not valid JSON") from exc
    try:
        validator.validate(value)
    except jsonschema_exceptions.ValidationError as exc:
        raise RuntimeError(
            "generation response does not match response_schema"
        ) from exc
    return response


def _anthropic_response(response: Any) -> GenerationResponse:
    text_parts: list[str] = []
    tool_calls: list[GenerationToolCall] = []
    for block in response.content:
        block_type = getattr(block, "type", None)
        if block_type == "text":
            text_parts.append(block.text)
        elif block_type == "tool_use":
            tool_calls.append(
                GenerationToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=dict(block.input),
                )
            )
    if hasattr(response, "assistant_message"):
        assistant_message = response.assistant_message
    else:
        assistant_message = {
            "role": "assistant",
            "content": [
                {
                    "type": "provider_state",
                    "provider": "anthropic",
                    "state": {
                        "content": [
                            block.model_dump(mode="json", exclude_none=True)
                            for block in response.content
                        ]
                    },
                }
            ],
        }
    return GenerationResponse(
        text="".join(text_parts),
        model=response.model,
        stop_reason=response.stop_reason,
        tool_calls=tool_calls,
        assistant_message=assistant_message,
    )


def _gemini_stop_reason(finish_reason: str, *, has_tool_calls: bool) -> str:
    if finish_reason == "MAX_TOKENS":
        return "max_tokens"
    if finish_reason in {
        "SAFETY",
        "BLOCKLIST",
        "PROHIBITED_CONTENT",
        "SPII",
        "IMAGE_SAFETY",
        "RECITATION",
        "PROMPT_BLOCKED",
    }:
        return "refusal"
    if finish_reason == "STOP":
        return "tool_use" if has_tool_calls else "end_turn"
    raise RuntimeError(f"Gemini generation stopped unexpectedly: {finish_reason}")


def generate(
    *,
    messages: list[dict[str, Any]],
    system: str | None = None,
    max_output_tokens: int = 16000,
    effort: str | None = None,
    response_schema: dict[str, Any] | None = None,
    tools: list[dict[str, Any]] | None = None,
) -> GenerationResponse:
    if max_output_tokens <= 0:
        raise RuntimeError("max_output_tokens must be positive")
    if effort is not None and effort not in ("low", "medium", "high"):
        raise RuntimeError("generation effort must be low, medium, or high")
    provider = _get_required_env("APP_AI_PROVIDER")
    adapter_messages = _adapter_messages(messages)
    combined_system = _combine_system(system, response_schema)
    schema_validator = _schema_validator(response_schema)

    if provider in {"vertex_ai_claude", "aws_bedrock_claude"}:
        kwargs: dict[str, Any] = {}
        if combined_system:
            kwargs["system"] = combined_system
        if effort:
            kwargs["output_config"] = {"effort": effort}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = {"type": "auto"}
        response = create_anthropic_message(
            messages=_anthropic_messages(adapter_messages),
            max_tokens=max_output_tokens,
            **kwargs,
        )
        return _validate_structured_response(
            _anthropic_response(response), schema_validator
        )

    if provider == "azure_foundry_openai":
        response = create_openai_generation(
            messages=adapter_messages,
            system=combined_system,
            max_tokens=max_output_tokens,
            effort=effort,
            tools=tools,
        )
        return _validate_structured_response(
            GenerationResponse(
                text=response.text,
                model=response.model,
                stop_reason=response.stop_reason,
                tool_calls=[
                    GenerationToolCall(
                        id=call.id,
                        name=call.name,
                        arguments=call.arguments,
                    )
                    for call in response.tool_calls
                ],
                assistant_message=response.assistant_message,
            ),
            schema_validator,
        )

    if provider == "vertex_ai_gemini":
        response = generate_gemini_message(
            messages=adapter_messages,
            system=combined_system,
            max_tokens=max_output_tokens,
            effort=effort,
            tools=tools,
        )
        tool_calls = [
            GenerationToolCall(
                id=call.id,
                name=call.name,
                arguments=call.arguments,
            )
            for call in response.function_calls
        ]
        return _validate_structured_response(
            GenerationResponse(
                text=response.text,
                model=response.model,
                stop_reason=_gemini_stop_reason(
                    response.finish_reason,
                    has_tool_calls=bool(tool_calls),
                ),
                tool_calls=tool_calls,
                assistant_message=response.assistant_message,
            ),
            schema_validator,
        )

    raise RuntimeError(f"Unsupported APP_AI_PROVIDER: {provider}")
