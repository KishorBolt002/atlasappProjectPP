"""Same-origin FastAPI routes for custom agent interfaces built on the Agent SDK."""

from typing import TypedDict
from urllib.parse import quote
from uuid import UUID

import httpx
from agent_sdk import AgentSDKError, AsyncAgentClient
from agent_sdk.automation import USER_SESSION
from fastapi import APIRouter, HTTPException, Request, Security
from starlette.background import BackgroundTask
from starlette.responses import Response, StreamingResponse

from .client import ATLAS_USER_SESSION_HEADER, AgentRegistry, PublicAgent

# Every route declares the user session it acts as, which keeps these routes out
# of automations; _user_session enforces it.
router = APIRouter(
    prefix="/api/_atlas/agents", tags=["agents"], dependencies=[Security(USER_SESSION)]
)

_FORWARDED_RESPONSE_HEADERS = frozenset(
    {"cache-control", "content-disposition", "content-type", "etag", "last-modified"}
)


class PublicAgentResponse(TypedDict):
    id: str
    slug: str
    name: str
    description: str


def _public_agent_response(agent: PublicAgent) -> PublicAgentResponse:
    return {
        "id": agent.id,
        "slug": agent.slug,
        "name": agent.name,
        "description": agent.description,
    }


def _user_session(request: Request) -> str:
    session_token = request.headers.get(ATLAS_USER_SESSION_HEADER, "").strip()
    if not session_token:
        raise HTTPException(status_code=401, detail="user session is required")
    return session_token


def _registry() -> AgentRegistry:
    try:
        return AgentRegistry()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=500, detail="agent SDK is not configured"
        ) from exc


async def _close_upstream(response: httpx.Response, client: AsyncAgentClient) -> None:
    await response.aclose()
    await client.close()


async def _proxy(
    request: Request,
    agent_identifier: str,
    upstream_path: str,
    *,
    stream: bool = False,
) -> Response:
    user_session = _user_session(request)
    content_type = request.headers.get("content-type")
    content = request.stream() if request.method not in {"GET", "HEAD"} else None
    try:
        client = _registry().client(agent_identifier, user_session)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="agent not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="user session is required") from exc

    try:
        # Every proxied response streams back unread, but only genuinely
        # streaming routes may read without a deadline.
        upstream = await client.request(
            request.method,
            upstream_path,
            query=tuple(request.query_params.multi_items()),
            content=content,
            headers={"Content-Type": content_type} if content_type else None,
            stream=True,
            raise_for_status=False,
            timeout=None if stream else httpx.Timeout(300, connect=10),
        )
    except AgentSDKError as exc:
        await client.close()
        raise HTTPException(status_code=502, detail="agent request failed") from exc
    except BaseException:
        # Aborted uploads (ClientDisconnect) and task cancellation are not SDK
        # errors; the proxy-owned client must still be released.
        await client.close()
        raise

    headers = {
        name: value
        for name, value in upstream.headers.items()
        if name.lower() in _FORWARDED_RESPONSE_HEADERS
    }
    if stream:
        return StreamingResponse(
            upstream.aiter_raw(),
            status_code=upstream.status_code,
            headers=headers,
            background=BackgroundTask(_close_upstream, upstream, client),
        )

    try:
        body = await upstream.aread()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="agent response failed") from exc
    finally:
        await _close_upstream(upstream, client)
    return Response(content=body, status_code=upstream.status_code, headers=headers)


@router.get("")
async def list_agents(request: Request) -> list[PublicAgentResponse]:
    """List the app's agents without exposing credentials or upstream URLs."""
    _user_session(request)
    return [_public_agent_response(agent) for agent in _registry().list_agents()]


@router.get("/paired")
async def get_paired_agent(request: Request) -> PublicAgentResponse:
    """Return the agent built in this app's Build chat."""
    _user_session(request)
    registry = _registry()
    try:
        return _public_agent_response(registry.paired_agent())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="paired agent not found") from exc


@router.get("/{agent_identifier}/threads")
async def list_threads(request: Request, agent_identifier: str) -> Response:
    return await _proxy(request, agent_identifier, "/api/threads")


@router.post("/{agent_identifier}/threads")
async def create_thread(request: Request, agent_identifier: str) -> Response:
    return await _proxy(request, agent_identifier, "/api/threads")


@router.get("/{agent_identifier}/threads/{thread_id}")
async def get_thread(
    request: Request, agent_identifier: str, thread_id: str
) -> Response:
    return await _proxy(
        request, agent_identifier, f"/api/threads/{quote(thread_id, safe='')}"
    )


@router.patch("/{agent_identifier}/threads/{thread_id}")
async def rename_thread(
    request: Request, agent_identifier: str, thread_id: str
) -> Response:
    return await _proxy(
        request, agent_identifier, f"/api/threads/{quote(thread_id, safe='')}"
    )


@router.delete("/{agent_identifier}/threads/{thread_id}")
async def delete_thread(
    request: Request, agent_identifier: str, thread_id: str
) -> Response:
    return await _proxy(
        request, agent_identifier, f"/api/threads/{quote(thread_id, safe='')}"
    )


@router.post("/{agent_identifier}/threads/{thread_id}/pin")
async def pin_thread(
    request: Request, agent_identifier: str, thread_id: str
) -> Response:
    return await _proxy(
        request, agent_identifier, f"/api/threads/{quote(thread_id, safe='')}/pin"
    )


@router.delete("/{agent_identifier}/threads/{thread_id}/pin")
async def unpin_thread(
    request: Request, agent_identifier: str, thread_id: str
) -> Response:
    return await _proxy(
        request, agent_identifier, f"/api/threads/{quote(thread_id, safe='')}/pin"
    )


@router.post("/{agent_identifier}/threads/{thread_id}/uploads")
async def upload_file(
    request: Request, agent_identifier: str, thread_id: str
) -> Response:
    return await _proxy(
        request,
        agent_identifier,
        f"/api/threads/{quote(thread_id, safe='')}/uploads",
    )


@router.get("/{agent_identifier}/threads/{thread_id}/files")
async def list_thread_files(
    request: Request, agent_identifier: str, thread_id: str
) -> Response:
    return await _proxy(
        request, agent_identifier, f"/api/threads/{quote(thread_id, safe='')}/files"
    )


@router.get("/{agent_identifier}/threads/{thread_id}/files/{file_id}/content")
async def download_thread_file(
    request: Request, agent_identifier: str, thread_id: str, file_id: str
) -> Response:
    return await _proxy(
        request,
        agent_identifier,
        (
            f"/api/threads/{quote(thread_id, safe='')}"
            f"/files/{quote(file_id, safe='')}/content"
        ),
        stream=True,
    )


@router.post("/{agent_identifier}/chat")
async def send_message(request: Request, agent_identifier: str) -> Response:
    return await _proxy(request, agent_identifier, "/api/chat")


@router.post("/{agent_identifier}/chat/stream")
async def stream_message(request: Request, agent_identifier: str) -> Response:
    return await _proxy(request, agent_identifier, "/api/chat/stream", stream=True)


@router.post("/{agent_identifier}/chat/resume")
async def resume_message(request: Request, agent_identifier: str) -> Response:
    return await _proxy(request, agent_identifier, "/api/chat/resume", stream=True)


@router.post("/{agent_identifier}/chat/attach")
async def attach_message(request: Request, agent_identifier: str) -> Response:
    return await _proxy(request, agent_identifier, "/api/chat/attach", stream=True)


@router.post("/{agent_identifier}/chat/stop")
async def stop_message(request: Request, agent_identifier: str) -> Response:
    return await _proxy(request, agent_identifier, "/api/chat/stop")


@router.post("/{agent_identifier}/calls/{call_id}")
async def get_call(request: Request, agent_identifier: str, call_id: UUID) -> Response:
    return await _proxy(
        request, agent_identifier, f"/api/calls/{quote(str(call_id), safe='')}"
    )


@router.post("/{agent_identifier}/calls/{call_id}/events")
async def subscribe_call(
    request: Request, agent_identifier: str, call_id: UUID
) -> Response:
    return await _proxy(
        request,
        agent_identifier,
        f"/api/calls/{quote(str(call_id), safe='')}/events",
        stream=True,
    )


@router.post("/{agent_identifier}/calls/{call_id}/recording")
async def call_recording(
    request: Request, agent_identifier: str, call_id: UUID
) -> Response:
    return await _proxy(
        request,
        agent_identifier,
        f"/api/calls/{quote(str(call_id), safe='')}/recording",
        stream=True,
    )


@router.post("/{agent_identifier}/calls/{call_id}/delete")
async def delete_call(
    request: Request, agent_identifier: str, call_id: UUID
) -> Response:
    return await _proxy(
        request, agent_identifier, f"/api/calls/{quote(str(call_id), safe='')}/delete"
    )
