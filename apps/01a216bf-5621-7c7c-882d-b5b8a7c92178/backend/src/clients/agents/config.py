"""Strict loader for the platform-mounted agent SDK configuration."""

from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

AGENTS_CONFIG_PATH = Path("/workspace/secrets/agents/config.json")


class MountedAgent(BaseModel):
    """One agent endpoint the app calls as the current user."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    slug: str
    name: str
    description: str
    base_url: HttpUrl = Field(repr=False, exclude=True)


class MountedAgentsConfig(BaseModel):
    """The complete agent SDK configuration mounted for this app."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    agents: tuple[MountedAgent, ...]


@lru_cache(maxsize=1)
def load_mounted_agents() -> MountedAgentsConfig:
    """Load and validate the mounted configuration exactly once."""
    if not AGENTS_CONFIG_PATH.is_file():
        raise RuntimeError(f"agent SDK config is not mounted at {AGENTS_CONFIG_PATH}")

    try:
        config = MountedAgentsConfig.model_validate_json(
            AGENTS_CONFIG_PATH.read_bytes()
        )
    except Exception as exc:
        raise RuntimeError("agent SDK config is invalid") from exc

    seen_ids: set[str] = set()
    seen_slugs: set[str] = set()
    for agent in config.agents:
        if not agent.id or agent.id != agent.id.strip():
            raise RuntimeError("mounted agent ID is required")
        try:
            if str(UUID(agent.id)) != agent.id:
                raise ValueError
        except ValueError as exc:
            raise RuntimeError(f"mounted agent ID is invalid: {agent.id}") from exc
        if not agent.slug or agent.slug != agent.slug.strip():
            raise RuntimeError(f"mounted agent slug is required for agent {agent.id}")
        if not agent.name or agent.name != agent.name.strip():
            raise RuntimeError(f"mounted agent name is required for agent {agent.id}")
        parsed_url = urlsplit(str(agent.base_url))
        if parsed_url.scheme != "https":
            raise RuntimeError(
                f"mounted agent base URL must use HTTPS for agent {agent.id}"
            )
        if parsed_url.port not in {None, 443}:
            raise RuntimeError(
                f"mounted agent base URL must use the default HTTPS port for agent {agent.id}"
            )
        if parsed_url.username is not None or parsed_url.password is not None:
            raise RuntimeError(
                f"mounted agent base URL must not contain credentials for agent {agent.id}"
            )
        if parsed_url.query or parsed_url.fragment:
            raise RuntimeError(
                f"mounted agent base URL must not contain a query or fragment for agent {agent.id}"
            )
        if parsed_url.path not in {"", "/"}:
            raise RuntimeError(
                f"mounted agent base URL must not contain a path for agent {agent.id}"
            )
        if agent.id in seen_ids:
            raise RuntimeError(f"duplicate mounted agent ID {agent.id}")
        if agent.slug in seen_slugs:
            raise RuntimeError(f"duplicate mounted agent slug {agent.slug}")
        seen_ids.add(agent.id)
        seen_slugs.add(agent.slug)

    return config
