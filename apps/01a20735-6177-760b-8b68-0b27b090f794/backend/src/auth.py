"""
Authorization utilities for Atlas Build apps.

Provides header-based user resolution and role-based access control.
Authentication is handled by the platform - this module only handles authorization.

The platform sets these headers on every request:
- Atlas-User-Email: authenticated user's email
- Atlas-User-Name-B64: base64-encoded user name
- X-Atlas-Client-IP: the visitor's IP address, read through get_client_ip

Phone callers the app's agent talks to have no Atlas account. The platform
admits them only to routes under /api/caller/public and, once the agent has
verified who they are, /api/caller/verified; serve those routes with
get_public_caller and get_verified_caller. An Atlas user trying the agent in
its own chat reaches the same routes the same way.

Usage:
    from src.auth import get_current_user, require_role

    @router.get("/api/admin/users")
    def list_users(user: Annotated[CurrentUser, Depends(require_role("admin"))]):
        ...

    @router.get("/api/dashboard")
    def dashboard(user: Annotated[CurrentUser, Depends(get_current_user)]):
        ...
"""

import base64
import json
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.dependencies import get_db

# Atlas platform headers set by the internal router
ATLAS_USER_ID_HEADER = "Atlas-User-Id"
ATLAS_USER_EMAIL_HEADER = "Atlas-User-Email"
ATLAS_USER_NAME_B64_HEADER = "Atlas-User-Name-B64"
ATLAS_CALLER_VERIFIED_HEADER = "Atlas-Caller-Verified-B64"
ATLAS_CALL_REFERENCE_HEADER = "Atlas-Call-Reference"
ATLAS_CALL_REFERENCE_ACK_HEADER = "Atlas-Call-Reference-Ack"
ATLAS_CLIENT_IP_HEADER = "X-Atlas-Client-IP"

# The routes the platform opens to the agent's phone callers.
CALLER_PUBLIC_SCOPE = "/api/caller/public"
CALLER_VERIFIED_SCOPE = "/api/caller/verified"

# API key requests use this email - always treated as admin
API_KEY_EMAIL = "build@atlas.foo"

# Default role for platform-authenticated users not in the app_users table.
# Set to a role name (e.g., "viewer") to allow access with limited permissions.
# Set to None to deny access to users not in the user management table.
DEFAULT_ROLE: str | None = "viewer"


@dataclass
class CurrentUser:
    """Resolved user context from platform headers and app authorization."""

    email: str
    name: str
    role: str
    # The user's stable Atlas ID. Pass it as atlas_user_id when calling a
    # per-user MCP server so the platform resolves this user's own credential.
    atlas_user_id: str


def get_current_user(
    request: Request, db: Annotated[Session, Depends(get_db)]
) -> CurrentUser:
    """Resolve the current user from platform headers and the app's user table.

    The platform guarantees the user is authenticated. This dependency resolves
    their authorization role from the app's user management table.
    """
    from src.models import AppUser  # ty: ignore[unresolved-import]

    email = request.headers.get(ATLAS_USER_EMAIL_HEADER, "").lower()
    if not email:
        raise HTTPException(status_code=401, detail="Missing user identity")

    atlas_user_id = request.headers.get(ATLAS_USER_ID_HEADER, "")

    name_b64 = request.headers.get(ATLAS_USER_NAME_B64_HEADER, "")
    name = ""
    if name_b64:
        try:
            name = base64.b64decode(name_b64).decode("utf-8")
        # binascii.Error and UnicodeDecodeError are both ValueError subclasses;
        # the name is cosmetic, so a malformed header falls back to empty.
        except ValueError:
            name = ""

    # API key users are always admin
    if email == API_KEY_EMAIL:
        return CurrentUser(
            email=email, name="API Key", role="admin", atlas_user_id=atlas_user_id
        )

    app_user = db.query(AppUser).filter(func.lower(AppUser.email) == email).first()
    if app_user:
        return CurrentUser(
            email=app_user.email,
            name=app_user.name,
            role=app_user.role,
            atlas_user_id=atlas_user_id,
        )

    # User is authenticated by platform but not in app user management
    if DEFAULT_ROLE is not None:
        return CurrentUser(
            email=email, name=name, role=DEFAULT_ROLE, atlas_user_id=atlas_user_id
        )

    raise HTTPException(status_code=403, detail="Access denied")


def get_signed_in_email(request: Request) -> str:
    """Return the signed-in user's email without any role lookup.

    The app has a single role: every platform-authenticated user can do
    everything, so only the presence of an identity is checked.
    """
    email = request.headers.get(ATLAS_USER_EMAIL_HEADER, "").strip().lower()
    if not email:
        raise HTTPException(status_code=401, detail="Missing user identity")
    return email


def require_role(*allowed_roles: str):
    """Dependency that checks the current user has one of the allowed roles.

    Usage:
        @router.get("/api/admin/settings")
        def admin_settings(user: Annotated[CurrentUser, Depends(require_role("admin"))]):
            ...

        @router.put("/api/items/{id}")
        def update_item(user: Annotated[CurrentUser, Depends(require_role("admin", "editor"))]):
            ...
    """

    def check_role(
        user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return check_role


def get_client_ip(request: Request) -> str:
    """Return the IP address of the visitor who sent the request.

    The platform's front door sets it on each request and replaces a copy the
    visitor sends, which suits keying rate limits or audit records on it.
    """
    client_ip = request.headers.get(ATLAS_CLIENT_IP_HEADER, "").strip()
    if not client_ip:
        raise HTTPException(status_code=500, detail="Missing client IP address")
    return client_ip


@dataclass
class Caller:
    """Whom the agent is talking to on a route the platform opens to callers.

    verified holds whom the agent verified the caller as, exactly as its caller
    verification returned it (for example {"patient_id": "P-1042"}), and is
    empty on public caller routes.
    """

    verified: dict[str, str]


def _require_caller_route(request: Request, scope: str) -> None:
    if not request.headers.get(ATLAS_USER_ID_HEADER):
        raise HTTPException(status_code=401, detail="Not authenticated")
    path = request.url.path
    if path != scope and not path.startswith(scope + "/"):
        raise HTTPException(
            status_code=500, detail=f"Caller route must live under {scope}"
        )


def get_public_caller(request: Request) -> Caller:
    """Serve a route under /api/caller/public to any phone caller.

    Return only what anyone may hear, such as opening hours or locations.
    """
    _require_caller_route(request, CALLER_PUBLIC_SCOPE)
    return Caller(verified={})


def get_verified_caller(request: Request) -> Caller:
    """Serve a route under /api/caller/verified to a verified phone caller.

    Scope every query by caller.verified, never by an identifier in the path,
    query, or body: the platform sets it from the signed session, so the route
    can act only for the person the caller was verified as.
    """
    _require_caller_route(request, CALLER_VERIFIED_SCOPE)
    try:
        verified = json.loads(
            base64.b64decode(
                request.headers.get(ATLAS_CALLER_VERIFIED_HEADER, ""), validate=True
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=403, detail="The caller is not verified"
        ) from exc
    if not isinstance(verified, dict) or not verified:
        raise HTTPException(status_code=403, detail="The caller is not verified")
    return Caller(verified=verified)


def get_phone_call_reference(request: Request, response: Response) -> str | None:
    """Return the private phone call reference on a verified caller operation.

    Store it with the caller's app record. Authorize the record's viewer before
    exchanging it for SDK access, and never return this private reference to
    the browser or include it in a tool response.
    Pass the actual returned response, or the injected response when returning
    data. The successful response acknowledges that this app retained the reference.
    """
    get_verified_caller(request)
    reference = request.headers.get(ATLAS_CALL_REFERENCE_HEADER) or None
    if reference:
        response.headers[ATLAS_CALL_REFERENCE_ACK_HEADER] = reference
    return reference
