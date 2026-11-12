"""
App configuration helpers for reading from project.json (workspace) or environment variables (Sandbox and Production services).
"""

import json
import os

# nosemgrep: workspace.static.semgrep-rules.backend.no-workspace-prefix-paths
PROJECT_FILE = "/workspace/builder/project.json"


def _derive_db_schema_from_app_id(app_id: str) -> str:
    """Derive database schema name from app_id.

    Format: app_{uuid_with_underscores}_workspace
    """
    return f"app_{app_id.replace('-', '_')}_workspace"


def _workspace_app_id() -> str | None:
    """Read app_id from project.json in workspace containers, else None."""
    if os.environ.get("IS_WORKSPACE") == "true" and os.path.exists(PROJECT_FILE):
        with open(PROJECT_FILE, "r") as f:
            # nosemgrep: workspace.static.semgrep-rules.backend.json-unsafe-key-access
            return json.load(f)["app_id"]
    return None


def get_app_id() -> str:
    """Get this app's own ID.

    Copying, branching, or installing the project gives the app a new ID, so
    code that names the app itself reads it here instead of writing it down.
    In workspace containers, reads app_id from project.json.
    In Sandbox and Production services, reads the APP_ID environment variable.
    """
    app_id = _workspace_app_id()
    if app_id is not None:
        return app_id
    return os.environ["APP_ID"]


def get_db_schema() -> str:
    """Get database schema name.

    In workspace containers, derives from app_id in project.json.
    In Sandbox and Production services, reads from DB_SCHEMA environment variable.
    """
    app_id = _workspace_app_id()
    if app_id is not None:
        return _derive_db_schema_from_app_id(app_id)
    return os.environ["DB_SCHEMA"]
