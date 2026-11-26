"""Server-side entry point to the Agent SDK for the app's mounted agents."""

import json
import os
from dataclasses import dataclass

from agent_sdk import AsyncAgentClient

from src.clients.user_sessions import session_for_agent

from .config import MountedAgent, load_mounted_agents

ATLAS_USER_SESSION_HEADER = "X-Atlas-User-Session"
PAIRED_AGENT_ENV_VAR = "PAIRED_AGENT_ID"
AGENT_RUNTIME_IDS_ENV_VAR = "AGENT_RUNTIME_IDS"


@dataclass(frozen=True)
class PublicAgent:
    """Mounted-agent metadata safe to return to a browser."""

    id: str
    slug: str
    name: str
    description: str


def _public_agent(agent: MountedAgent) -> PublicAgent:
    return PublicAgent(
        id=agent.id,
        slug=agent.slug,
        name=agent.name,
        description=agent.description,
    )


class AgentRegistry:
    """Resolves mounted agents into authenticated Agent SDK clients."""

    def __init__(self) -> None:
        config = load_mounted_agents()
        self._agents_by_id = {agent.id: agent for agent in config.agents}
        self._agents_by_slug = {agent.slug: agent for agent in config.agents}
        # A copied app names an agent it was copied with by the original's ID,
        # while that agent identifies itself by its own runtime ID. The platform
        # sets the map from each such name to its runtime ID wherever it mounts
        # the agents.
        try:
            runtime_ids = json.loads(os.environ[AGENT_RUNTIME_IDS_ENV_VAR])
        except (KeyError, ValueError) as exc:
            raise RuntimeError("agent runtime IDs are not configured") from exc
        self._agents_by_runtime_id = {
            runtime_id: self._agents_by_id[agent_id]
            for agent_id, runtime_id in runtime_ids.items()
            if agent_id in self._agents_by_id
        }
        self._runtime_ids: dict[str, str] = runtime_ids

    def list_agents(self) -> list[PublicAgent]:
        """Return deterministic browser-safe metadata for every mounted agent."""
        return [
            _public_agent(agent)
            for agent in sorted(self._agents_by_id.values(), key=lambda item: item.id)
        ]

    @property
    def paired_agent_id(self) -> str:
        """ID of the agent built in this app's Build chat.

        Copying, branching, or installing the project gives that agent a new ID,
        so code reads it here instead of naming an agent. Raises KeyError when
        the app has no paired agent or it is not mounted yet.
        """
        agent_id = os.environ.get(PAIRED_AGENT_ENV_VAR, "").strip()
        if not agent_id:
            raise KeyError("this app has no paired agent")
        if agent_id not in self._agents_by_id:
            raise KeyError(f"paired agent {agent_id} is not mounted")
        return agent_id

    def paired_agent(self) -> PublicAgent:
        """Browser-safe metadata of the agent built in this app's Build chat."""
        return _public_agent(self._agents_by_id[self.paired_agent_id])

    def _resolve(self, identifier: str) -> MountedAgent:
        """Resolve an agent by its exact ID, the ID it runs as, or its exact slug."""
        normalized = identifier.strip()
        if not normalized:
            raise KeyError("agent identifier is required")
        agent = self._agents_by_id.get(normalized)
        if agent is None:
            agent = self._agents_by_runtime_id.get(normalized)
        if agent is None:
            agent = self._agents_by_slug.get(normalized)
        if agent is None:
            raise KeyError(f"agent {normalized} was not found")
        return agent

    def client(self, identifier: str, user_session: str) -> AsyncAgentClient:
        """Return an Agent SDK client for one mounted agent, acting as the given user.

        The agent applies that user's own access. The caller owns the returned
        client and must close it after the last response body has been consumed.
        """
        agent = self._resolve(identifier)
        runtime_id = self._runtime_ids.get(agent.id, agent.id)
        return AsyncAgentClient(
            base_url=str(agent.base_url),
            default_headers={
                ATLAS_USER_SESSION_HEADER: session_for_agent(user_session, runtime_id)
            },
        )
