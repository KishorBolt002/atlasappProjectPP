"""The sessions this app's backend presents to the apps and agents it calls.

A call to a connected app or agent acts as the person this app is serving, so
the called runtime applies that person's own role. Sandbox and Production
services sign that person's session for the target with the organization's
session key, as the platform's own sessions are signed; the target accepts
only a session scoped to itself. A request an automation sends carries the
automation's delegation instead, which a call to a connected app forwards once
it covers that app, so the app acts as the person the automation runs as. A
workspace holds no session key, so the platform stages the builder's session
for each connected app and agent there.
"""

import os
from collections.abc import Generator
from pathlib import Path

import httpx
import jwt
from agent_sdk.automation_auth import AUTOMATION_GRANT_HEADER, authorize_automation
from agent_sdk.user_sessions import (
    current_automation_grant,
    current_user_session,
    scoped_user_session,
)

from src.app_config import get_app_id

USER_SESSION_HEADER = "X-Atlas-User-Session"
# A phone caller's session names the call, not a person a called runtime knows.
CALLER_SUBJECT_PREFIX = "caller:"
# nosemgrep: workspace.static.semgrep-rules.backend.no-workspace-prefix-paths
STAGED_APP_SESSIONS = Path("/workspace/work/connected-app-sessions")
# nosemgrep: workspace.static.semgrep-rules.backend.no-workspace-prefix-paths
STAGED_AGENT_SESSIONS = Path("/workspace/work/connected-agent-sessions")


class ConnectedAppAuth(httpx.Auth):
    """Sends each request to a connected app as the person this app serves.

    The session, or an automation's delegation, is resolved when the request
    is sent, not when the client is built, so a client kept across requests
    carries whoever each request serves.
    """

    def __init__(self, app_id: str) -> None:
        if not app_id.strip():
            raise ValueError("connected app ID is required")
        self._app_id = app_id.strip()

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response]:
        grant = current_automation_grant()
        if grant is None:
            request.headers[USER_SESSION_HEADER] = session_for_app(self._app_id)
        else:
            authorize_automation(grant, "app", self._app_id)
            request.headers[AUTOMATION_GRANT_HEADER] = grant
        yield request


def session_for_app(app_id: str) -> str:
    """Return the session of the person this request serves, for app app_id.

    app_id is the ID the connected app runs as, not the ID this app's code
    names it by when the two differ. Raises when no person is behind the call.
    """
    target = app_id.strip()
    if not target:
        raise ValueError("connected app ID is required")
    if os.environ.get("IS_WORKSPACE") == "true":
        return _staged_session("app", target)
    return _signed_session("app", target, current_user_session())


def session_for_agent(user_session: str, agent_id: str) -> str:
    """Return the current person's session for the connected agent agent_id.

    agent_id is the ID the agent runs as.
    """
    return _session_for("agent", agent_id, user_session)


def _session_for(kind: str, target_id: str, user_session: str) -> str:
    target = target_id.strip()
    if not target:
        raise ValueError(f"connected {kind} ID is required")
    session = user_session.strip()
    if not session:
        raise ValueError("atlas user session is required")
    if os.environ.get("IS_WORKSPACE") == "true":
        return _staged_session(kind, target)
    return _signed_session(kind, target, session)


def _staged_session(kind: str, target: str) -> str:
    root, file_name = (
        (STAGED_APP_SESSIONS, "runtime-session")
        if kind == "app"
        else (STAGED_AGENT_SESSIONS, "agent-session")
    )
    path = root / target.lower() / file_name
    if not path.is_file():
        raise RuntimeError(f"no session is staged for connected {kind} {target}")
    token = path.read_text().strip()
    if not token:
        raise RuntimeError(f"the session staged for connected {kind} {target} is empty")
    return token


def _signed_session(kind: str, target: str, session: str) -> str:
    secret = os.environ["JWT_SECRET"]
    organization_id = os.environ["ORGANIZATION_ID"]
    app_id = get_app_id()
    try:
        claims = jwt.decode(
            session,
            secret,
            algorithms=["HS256"],
            options={"require": ["sub", "org", "exp"]},
        )
    except jwt.InvalidTokenError as exc:
        raise ValueError("atlas user session is invalid") from exc
    subject = claims["sub"]
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("atlas user session has no person")
    if subject.startswith(CALLER_SUBJECT_PREFIX):
        raise ValueError("a phone caller cannot call connected apps or agents")
    if claims["org"] != organization_id:
        raise ValueError("atlas user session belongs to another organization")
    # Only the session this app's runtime accepted for the current request
    # carries the person on to the apps and agents this app calls.
    if claims.get("app") != app_id:
        raise ValueError("atlas user session is not this app's")
    return scoped_user_session(
        claims, secret, kind=kind, target=target, extra={"calling_app": app_id}
    )
