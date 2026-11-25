/// <reference types="vite/client" />

interface AtlasAgentThreadSelectedDetail {
  agentId: string;
  threadId: string;
}

interface WindowEventMap {
  "atlas-agent-thread-selected": CustomEvent<AtlasAgentThreadSelectedDetail>;
}
