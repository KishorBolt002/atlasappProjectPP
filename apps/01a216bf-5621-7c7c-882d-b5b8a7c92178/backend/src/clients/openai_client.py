"""
Shared OpenAI client helpers for backend services.

This wrapper centralizes Azure Foundry OpenAI access for Azure apps in Sandbox and Production.
It uses Microsoft Entra ID and the v1 OpenAI-compatible endpoint instead of
static API keys or provider-specific SDK clients.

In the build workspace the Azure Foundry OpenAI endpoint is not reachable
(the workspace identity has no Azure OpenAI data actions), so generation and
document extraction are routed to Vertex AI Gemini in the Atlas platform
project. The OpenAI request shapes are translated to Gemini and the replies
are projected back onto the OpenAI response surface the callers read
(`.output_text` for responses, `.choices[0].message.content` for chat), so app
code is identical across workspace and cloud runtimes. Azure apps in Sandbox and Production
always call Azure Foundry directly.
"""

import json
import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from .azure_credential import build_bearer_token_provider
from .gemini_client import generate_gemini_message, generate_gemini_text

# max_tokens covers the full Gemini response when generation is routed to Vertex
# in the workspace; mirrors the provider-neutral generation default.
_WORKSPACE_MAX_TOKENS = 16000


@dataclass(frozen=True)
class OpenAIRuntimeConfig:
    client: OpenAI
    model: str


def _get_required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _is_workspace_runtime() -> bool:
    return os.environ.get("IS_WORKSPACE", "").strip().lower() == "true"


def _azure_openai_base_url() -> str:
    base_url = _get_required_env("APP_AZURE_FOUNDRY_OPENAI_BASE_URL").rstrip("/")
    return f"{base_url}/openai/v1/"


def get_openai_runtime_config() -> OpenAIRuntimeConfig:
    cloud_provider = _get_required_env("CLOUD_PROVIDER").lower()
    if cloud_provider != "azure":
        raise RuntimeError(f"Unsupported CLOUD_PROVIDER for OpenAI: {cloud_provider}")

    token_provider = build_bearer_token_provider("https://ai.azure.com/.default")
    client = OpenAI(
        base_url=_azure_openai_base_url(),
        api_key=token_provider,
    )
    return OpenAIRuntimeConfig(
        client=client,
        model=_get_required_env("APP_AZURE_FOUNDRY_MODEL"),
    )


def get_openai_client() -> OpenAI:
    return get_openai_runtime_config().client


def get_openai_model() -> str:
    return get_openai_runtime_config().model


@dataclass(frozen=True)
class _ChatMessage:
    content: str


@dataclass(frozen=True)
class _ChatChoice:
    message: _ChatMessage


@dataclass(frozen=True)
class _ChatCompletion:
    choices: list[_ChatChoice]


@dataclass(frozen=True)
class _Response:
    output_text: str


@dataclass(frozen=True)
class OpenAIGenerationToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class OpenAIGenerationResponse:
    text: str
    model: str
    stop_reason: str
    tool_calls: list[OpenAIGenerationToolCall]
    assistant_message: dict[str, Any] | None


def _data_url_to_anthropic_block(data_url: str) -> dict[str, Any]:
    if not data_url.startswith("data:"):
        raise RuntimeError("inline file data must be a base64 data URL")
    header, _, encoded = data_url.partition(",")
    if not encoded:
        raise RuntimeError("inline file data URL is missing base64 content")
    media_type = header[len("data:") :].split(";")[0].strip()
    if not media_type:
        raise RuntimeError("inline file data URL is missing a media type")
    source = {"type": "base64", "media_type": media_type, "data": encoded}
    if media_type.startswith("image/"):
        return {"type": "image", "source": source}
    return {"type": "document", "source": source}


def _translate_content_block(block: dict[str, Any]) -> dict[str, Any]:
    block_type = block.get("type")
    if block_type in ("text", "input_text", "output_text"):
        return {"type": "text", "text": block.get("text", "")}
    if block_type in ("input_file", "file"):
        file_data = block.get("file_data")
        if file_data is None and isinstance(block.get("file"), dict):
            file_data = block["file"].get("file_data")
        if not isinstance(file_data, str):
            raise RuntimeError("file content block is missing inline file_data")
        return _data_url_to_anthropic_block(file_data)
    if block_type in ("input_image", "image_url"):
        url = block.get("image_url")
        if isinstance(url, dict):
            url = url.get("url")
        if not isinstance(url, str):
            raise RuntimeError("image content block is missing an image url")
        return _data_url_to_anthropic_block(url)
    raise RuntimeError(f"unsupported content block type: {block_type}")


def _translate_content(content: Any) -> list[dict[str, Any]]:
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    if isinstance(content, list):
        return [_translate_content_block(block) for block in content]
    raise RuntimeError("message content must be a string or a list of blocks")


def _generic_openai_input(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    translated: list[dict[str, Any]] = []
    for message in messages:
        role = message.get("role")
        if role not in ("user", "assistant"):
            raise RuntimeError(f"unsupported OpenAI message role: {role}")
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
        if state_blocks:
            if not isinstance(content, list) or len(content) != 1:
                raise RuntimeError(
                    "generation provider state must be replayed unchanged"
                )
            block = state_blocks[0]
            if block.get("provider") != "openai":
                raise RuntimeError(
                    "generation history belongs to a different AI provider"
                )
            state = block.get("state")
            if not isinstance(state, dict):
                raise RuntimeError("OpenAI provider state must be an object")
            output = state.get("output")
            if not isinstance(output, list) or not all(
                isinstance(item, dict) for item in output
            ):
                raise RuntimeError("OpenAI provider state is missing output items")
            translated.extend(output)
            continue
        blocks = (
            [{"type": "text", "text": content}] if isinstance(content, str) else content
        )
        if not isinstance(blocks, list):
            raise TypeError("OpenAI message content must be text or blocks")
        message_content: list[dict[str, Any]] = []

        # Default arguments bind this iteration's role and block list at
        # definition time; the helper is only called within the same iteration.
        def flush_message_content(
            role: str = role,
            message_content: list[dict[str, Any]] = message_content,
        ) -> None:
            if message_content:
                translated.append({"role": role, "content": list(message_content)})
                message_content.clear()

        for block in blocks:
            if not isinstance(block, dict):
                raise TypeError("OpenAI message content blocks must be objects")
            block_type = block.get("type")
            if block_type == "text":
                text = block.get("text")
                if not isinstance(text, str):
                    raise RuntimeError("OpenAI text block is missing text")
                message_content.append(
                    {
                        "type": "input_text",
                        "text": text,
                    }
                )
            elif block_type in ("image", "document"):
                source = block.get("source")
                if not isinstance(source, dict) or source.get("type") != "base64":
                    raise RuntimeError(
                        "OpenAI media blocks must use inline base64 data"
                    )
                media_type = source.get("media_type")
                data = source.get("data")
                if not isinstance(media_type, str) or not media_type:
                    raise RuntimeError("OpenAI media block is missing its media type")
                if not isinstance(data, str) or not data:
                    raise RuntimeError("OpenAI media block is missing base64 data")
                data_url = f"data:{media_type};base64,{data}"
                if block_type == "image":
                    message_content.append(
                        {"type": "input_image", "image_url": data_url}
                    )
                else:
                    message_content.append(
                        {"type": "input_file", "file_data": data_url}
                    )
            elif block_type == "tool_use":
                tool_id = block.get("id")
                name = block.get("name")
                arguments = block.get("input")
                if not isinstance(tool_id, str) or not tool_id:
                    raise RuntimeError("OpenAI tool-use block is missing its id")
                if not isinstance(name, str) or not name:
                    raise RuntimeError("OpenAI tool-use block is missing its name")
                if not isinstance(arguments, dict):
                    raise RuntimeError("OpenAI tool-use input must be an object")
                flush_message_content()
                translated.append(
                    {
                        "type": "function_call",
                        "call_id": tool_id,
                        "name": name,
                        "arguments": json.dumps(arguments),
                    }
                )
            elif block_type == "tool_result":
                tool_id = block.get("tool_use_id")
                if not isinstance(tool_id, str) or not tool_id:
                    raise RuntimeError("OpenAI tool result is missing its tool-use id")
                output = block.get("content", "")
                if not isinstance(output, str):
                    output = json.dumps(output)
                flush_message_content()
                translated.append(
                    {
                        "type": "function_call_output",
                        "call_id": tool_id,
                        "output": output,
                    }
                )
            else:
                raise RuntimeError(
                    f"unsupported OpenAI content block type: {block_type}"
                )
        flush_message_content()
    return translated


def _generic_openai_tools(
    tools: list[dict[str, Any]] | None,
) -> list[dict[str, Any]] | None:
    if not tools:
        return None
    translated: list[dict[str, Any]] = []
    for tool in tools:
        name = tool.get("name")
        schema = tool.get("input_schema")
        if not isinstance(name, str) or not name:
            raise RuntimeError("OpenAI tools require a name")
        if not isinstance(schema, dict):
            raise TypeError(f"OpenAI tool {name} requires input_schema")
        item: dict[str, Any] = {
            "type": "function",
            "name": name,
            "parameters": schema,
        }
        description = tool.get("description")
        if isinstance(description, str) and description:
            item["description"] = description
        translated.append(item)
    return translated


def _openai_generation_stop_reason(response: Any, *, has_tool_calls: bool) -> str:
    for item in getattr(response, "output", []):
        if getattr(item, "type", None) != "message":
            continue
        if any(
            getattr(block, "type", None) == "refusal"
            for block in getattr(item, "content", [])
        ):
            return "refusal"
    status = getattr(response, "status", None)
    if status == "completed":
        return "tool_use" if has_tool_calls else "end_turn"
    if status == "incomplete":
        reason = getattr(getattr(response, "incomplete_details", None), "reason", None)
        if reason == "max_output_tokens":
            return "max_tokens"
        if reason == "content_filter":
            return "refusal"
        raise RuntimeError(f"OpenAI generation was incomplete: {reason}")
    raise RuntimeError(f"OpenAI generation failed with status: {status}")


def _openai_assistant_message(response: Any) -> dict[str, Any]:
    output: list[dict[str, Any]] = []
    for item in response.output:
        serialized = item.model_dump(mode="json", exclude_none=True)
        if not isinstance(serialized, dict):
            raise TypeError("OpenAI output item must serialize to an object")
        output.append(serialized)
    return {
        "role": "assistant",
        "content": [
            {
                "type": "provider_state",
                "provider": "openai",
                "state": {"output": output},
            }
        ],
    }


def create_openai_generation(
    *,
    messages: list[dict[str, Any]],
    system: str | None = None,
    max_tokens: int = _WORKSPACE_MAX_TOKENS,
    stop_sequences: list[str] | None = None,
    effort: str | None = None,
    tools: list[dict[str, Any]] | None = None,
) -> OpenAIGenerationResponse:
    if _is_workspace_runtime():
        response = generate_gemini_message(
            messages=messages,
            system=system,
            max_tokens=max_tokens,
            stop_sequences=stop_sequences,
            effort=effort,
            tools=tools,
        )
        tool_calls = [
            OpenAIGenerationToolCall(
                id=call.id,
                name=call.name,
                arguments=call.arguments,
            )
            for call in response.function_calls
        ]
        if response.finish_reason == "MAX_TOKENS":
            stop_reason = "max_tokens"
        elif response.finish_reason in {
            "SAFETY",
            "BLOCKLIST",
            "PROHIBITED_CONTENT",
            "SPII",
            "IMAGE_SAFETY",
            "RECITATION",
            "PROMPT_BLOCKED",
        }:
            stop_reason = "refusal"
        elif response.finish_reason == "STOP":
            stop_reason = "tool_use" if tool_calls else "end_turn"
        else:
            raise RuntimeError(
                f"Gemini generation stopped unexpectedly: {response.finish_reason}"
            )
        return OpenAIGenerationResponse(
            text=response.text,
            model=response.model,
            stop_reason=stop_reason,
            tool_calls=tool_calls,
            assistant_message=response.assistant_message,
        )

    runtime = get_openai_runtime_config()
    request: dict[str, Any] = {
        "model": runtime.model,
        "input": _generic_openai_input(messages),
        "max_output_tokens": max_tokens,
    }
    if system:
        request["instructions"] = system
    if stop_sequences:
        raise RuntimeError(
            "Azure Foundry OpenAI Responses does not support stop sequences"
        )
    if effort:
        request["reasoning"] = {"effort": effort}
    translated_tools = _generic_openai_tools(tools)
    if translated_tools:
        request["tools"] = translated_tools
    response = runtime.client.responses.create(**request)
    tool_calls: list[OpenAIGenerationToolCall] = []
    for item in response.output:
        if getattr(item, "type", None) != "function_call":
            continue
        arguments = json.loads(item.arguments)
        if not isinstance(arguments, dict):
            raise TypeError("OpenAI tool-call arguments must be an object")
        tool_calls.append(
            OpenAIGenerationToolCall(
                id=item.call_id,
                name=item.name,
                arguments=arguments,
            )
        )
    return OpenAIGenerationResponse(
        text=response.output_text,
        model=runtime.model,
        stop_reason=_openai_generation_stop_reason(
            response, has_tool_calls=bool(tool_calls)
        ),
        tool_calls=tool_calls,
        assistant_message=_openai_assistant_message(response),
    )


def _translate_messages(
    messages: Iterable[Mapping[str, Any]],
) -> tuple[str | None, list[dict[str, Any]]]:
    system_parts: list[str] = []
    translated: list[dict[str, Any]] = []
    for message in messages:
        role = message.get("role")
        content = message.get("content")
        if role in ("system", "developer"):
            for block in _translate_content(content):
                if block["type"] == "text":
                    system_parts.append(block["text"])
            continue
        translated.append({"role": role, "content": _translate_content(content)})
    system = "\n\n".join(part for part in system_parts if part) or None
    return system, translated


def _translate_response_input(
    response_input: Any,
) -> tuple[str | None, list[dict[str, Any]]]:
    if isinstance(response_input, str):
        return None, [
            {"role": "user", "content": [{"type": "text", "text": response_input}]}
        ]
    if isinstance(response_input, list):
        if (
            response_input
            and isinstance(response_input[0], dict)
            and "role" in response_input[0]
        ):
            return _translate_messages(response_input)
        # A bare list of content blocks is a single user turn.
        return None, [
            {
                "role": "user",
                "content": [
                    _translate_content_block(block) for block in response_input
                ],
            }
        ]
    raise RuntimeError("response input must be a string or a list")


def _workspace_max_tokens(kwargs: dict[str, Any]) -> int:
    for key in ("max_output_tokens", "max_completion_tokens", "max_tokens"):
        value = kwargs.get(key)
        if isinstance(value, int) and value > 0:
            return value
    return _WORKSPACE_MAX_TOKENS


def _structured_output_instruction(fmt: Any) -> str | None:
    """Translate an OpenAI structured-output format spec into a Gemini system
    instruction so the workspace path returns parseable JSON, matching the
    Azure cloud path that forwards `text={"format": ...}` / `response_format`.
    Handles both the Responses (`{"type": "json_schema", "schema": ...}`) and
    chat (`{"type": "json_schema", "json_schema": {"schema": ...}}`) shapes."""
    if not isinstance(fmt, Mapping):
        return None
    fmt_type = fmt.get("type")
    if fmt_type == "json_object":
        return "Respond with only a single valid JSON object, with no markdown fences or surrounding prose."
    if fmt_type == "json_schema":
        schema = fmt.get("schema")
        if schema is None and isinstance(fmt.get("json_schema"), Mapping):
            schema = fmt["json_schema"].get("schema")
        instruction = "Respond with only a single JSON value, with no markdown fences or surrounding prose."
        if schema is not None:
            instruction += (
                f" The JSON must conform to this JSON Schema: {json.dumps(schema)}"
            )
        return instruction
    return None


def _combine_system(*parts: str | None) -> str | None:
    return "\n\n".join(part for part in parts if part) or None


def _stop_sequences(kwargs: dict[str, Any]) -> list[str] | None:
    """Translate OpenAI `stop` (str or list of up to 4 strings) to Gemini
    `stop_sequences` for the workspace adapter."""
    stop = kwargs.get("stop")
    if isinstance(stop, str):
        return [stop]
    if isinstance(stop, list):
        sequences = [item for item in stop if isinstance(item, str)]
        return sequences or None
    return None


def _reject_unsupported_workspace_kwargs(kwargs: dict[str, Any]) -> None:
    """Fail fast on OpenAI options that change the response shape or transport in
    ways the Gemini workspace adapter cannot reproduce. The Azure cloud path
    forwards these, so silently dropping them would let an app pass workspace
    validation and then behave differently in Sandbox and Production. Sampling-only options
    (temperature, top_p, seed, ...) are intentionally not listed: they affect
    output style, not the response contract, so dropping them is harmless."""
    unsupported = [
        key
        for key in (
            "stream",
            "stream_options",
            "tools",
            "tool_choice",
            "functions",
            "function_call",
        )
        if kwargs.get(key)
    ]
    n = kwargs.get("n")
    if isinstance(n, int) and n > 1:
        unsupported.append("n")
    if unsupported:
        raise RuntimeError(
            "These OpenAI options are not supported in the build workspace, where "
            f"generation runs on Vertex AI Gemini: {', '.join(unsupported)}. They "
            "work in Sandbox and Production; remove them or guard them so the feature can "
            "be validated in the workspace."
        )


def create_openai_response(*, input: Any, **kwargs: Any) -> Any:
    if _is_workspace_runtime():
        _reject_unsupported_workspace_kwargs(kwargs)
        message_system, messages = _translate_response_input(input)
        instructions = kwargs.get("instructions")
        instructions = (
            instructions
            if isinstance(instructions, str) and instructions.strip()
            else None
        )
        text_param = kwargs.get("text")
        format_spec = (
            text_param.get("format") if isinstance(text_param, Mapping) else None
        )
        system = _combine_system(
            instructions, message_system, _structured_output_instruction(format_spec)
        )
        text, _ = generate_gemini_text(
            messages=messages,
            system=system,
            max_tokens=_workspace_max_tokens(kwargs),
            stop_sequences=_stop_sequences(kwargs),
        )
        return _Response(output_text=text)

    runtime_config = get_openai_runtime_config()
    return runtime_config.client.responses.create(
        model=runtime_config.model,
        input=input,
        **kwargs,
    )


def create_openai_chat_completion(
    *,
    messages: Iterable[ChatCompletionMessageParam],
    **kwargs: Any,
) -> Any:
    if _is_workspace_runtime():
        _reject_unsupported_workspace_kwargs(kwargs)
        message_system, translated = _translate_messages(messages)
        system = _combine_system(
            message_system,
            _structured_output_instruction(kwargs.get("response_format")),
        )
        text, _ = generate_gemini_text(
            messages=translated,
            system=system,
            max_tokens=_workspace_max_tokens(kwargs),
            stop_sequences=_stop_sequences(kwargs),
        )
        return _ChatCompletion(
            choices=[_ChatChoice(message=_ChatMessage(content=text))]
        )

    runtime_config = get_openai_runtime_config()
    return runtime_config.client.chat.completions.create(
        model=runtime_config.model,
        messages=messages,
        **kwargs,
    )
