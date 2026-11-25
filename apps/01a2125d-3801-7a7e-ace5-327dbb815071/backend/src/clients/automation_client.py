"""Session-bound source automation dependency for protected app endpoints, and
the resource catalog that tests validate this app's automation definitions
against."""

import asyncio
import json
import os
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Annotated, Any

import httpx
from agent_sdk.automation import USER_SESSION, automation_operations
from automation_sdk import (
    AsyncAutomationClient,
    AutomationAPIError,
    AutomationConnectionError,
    ModelChoice,
    ModelMetadata,
    ResourceCatalog,
    ResourceMetadata,
    RuntimeIDs,
    SubflowMetadata,
    runtime_http_client,
)
from automation_sdk.management import AGENT_MESSAGE_OPERATION
from fastapi import FastAPI, HTTPException, Security

# nosemgrep: workspace.static.semgrep-rules.backend.no-workspace-prefix-paths
DEPENDENCY_CONTEXT_FILE = Path("/workspace/builder/dependency-context.json")
APP_URLS_FILE = Path(__file__).parent / "apps" / "app_urls.json"

# Requests share one connection pool, so each reuses an open connection to the
# source runtime rather than opening a new TLS connection. A pool belongs to the
# event loop that opened it, so a request on another loop, such as a later test
# client's, replaces it.
_http_pool: tuple[asyncio.AbstractEventLoop, httpx.AsyncClient] | None = None


def _runtime_http_client() -> httpx.AsyncClient:
    global _http_pool
    loop = asyncio.get_running_loop()
    if _http_pool is None or _http_pool[0] is not loop:
        _http_pool = (loop, runtime_http_client())
    return _http_pool[1]


def _runtime_ids() -> RuntimeIDs:
    """Runtime IDs of the connected apps and agents this app's code names by
    other IDs."""
    app_urls = json.loads(APP_URLS_FILE.read_text(encoding="utf-8"))
    return RuntimeIDs(
        apps={
            app_id: urls["runtime_id"]
            for app_id, urls in app_urls.items()
            if "runtime_id" in urls
        },
        agents=json.loads(os.environ["AGENT_RUNTIME_IDS"]),
    )


async def automation_client(
    user_session: Annotated[str | None, Security(USER_SESSION)],
) -> AsyncIterator[AsyncAutomationClient]:
    session = "" if user_session is None else user_session.strip()
    if not session:
        raise HTTPException(status_code=401, detail="user session is required")
    try:
        client = AsyncAutomationClient.for_user_session(
            session, runtime_ids=_runtime_ids, http_client=_runtime_http_client()
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=403,
            detail="automation authoring is unavailable for this session",
        ) from exc
    try:
        async with client:
            yield client
    except AutomationAPIError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail={"error": exc.code, "message": str(exc)}
        ) from exc
    except AutomationConnectionError as exc:
        raise HTTPException(
            status_code=502, detail="source automation runtime is unavailable"
        ) from exc


def _app_resource(app_id: str, document: dict[str, Any]) -> ResourceMetadata:
    try:
        operations, unsupported = automation_operations(document)
    except ValueError as exc:
        # An API whose operations cannot be described is listed as unavailable,
        # with the reason, so only steps that call it fail.
        return ResourceMetadata(
            kind="app", id=app_id, url="", operations={}, unavailable=str(exc)
        )
    return ResourceMetadata.model_validate(
        {
            "kind": "app",
            "id": app_id,
            "url": "",
            "operations": operations,
            "unsupported_operations": unsupported,
        }
    )


def _place(document: dict[str, Any], reference: str, value: Any) -> None:
    parts = [
        part.replace("~1", "/").replace("~0", "~")
        for part in reference.removeprefix("#/").split("/")
    ]
    target = document
    for part in parts[:-1]:
        target = target.setdefault(part, {})
    target[parts[-1]] = value


def _contract_document(contract: dict[str, Any]) -> dict[str, Any]:
    """Rebuild the API document a connected app's contract describes."""
    document: dict[str, Any] = {"paths": {}}
    for entry in contract["operations"].values():
        definition = entry["definition"]
        item = document["paths"].setdefault(definition["path"], {})
        item[definition["method"]] = definition["operation"]
        if "path_parameters" in definition:
            item["parameters"] = definition["path_parameters"]
        for reference, value in entry["references"].items():
            _place(document, reference, value)
    return document


def workspace_catalog(
    application: FastAPI,
    *,
    models: list[ModelMetadata],
    default_model: ModelChoice,
    subflows: list[SubflowMetadata],
    http_apis: list[ResourceMetadata],
) -> ResourceCatalog:
    """Return the resources this app's automations can call, for testing definitions.

    Describes this app's operations from the current API of `application`, and
    every app and agent connected to it in the Build workspace. `models`,
    `default_model`, `subflows`, and `http_apis` are the source models, the
    source's automation model at its current location, subflows, and
    registered HTTP APIs the definitions use. Raises FileNotFoundError outside the Build workspace.
    """
    report = json.loads(DEPENDENCY_CONTEXT_FILE.read_text(encoding="utf-8"))
    app_id = report["app_id"]
    resources = [_app_resource(app_id, application.openapi())]
    agent_ids = [] if report["agent_id"] is None else [report["agent_id"]]
    # This app's own entry always comes from its current code.
    for dependency in report["available"]:
        if dependency["kind"] == "agent":
            agent_ids.append(dependency["id"])
        elif dependency["id"] != app_id:
            resources.append(
                _app_resource(
                    dependency["id"], _contract_document(dependency["contract"])
                )
            )
    for agent_id in dict.fromkeys(agent_ids):
        resources.append(
            ResourceMetadata(
                kind="agent",
                id=agent_id,
                url="",
                operations={"message": AGENT_MESSAGE_OPERATION},
            )
        )
    return ResourceCatalog(
        resources=[*resources, *http_apis],
        models=models,
        default_model=default_model,
        subflows=subflows,
    )
