import { reloadOnSignedOut } from "./session";

export interface CallAccess {
  id: string;
  token: string;
  expires_at: number;
  can_delete: boolean;
}

export interface CallTranscriptEntry {
  id: string;
  speaker: "caller" | "agent";
  text: string;
  timestamp: string;
  offset_ms: number;
  final: boolean;
  interrupted: boolean;
}

export type CallStatus = "verifying" | "active" | "completed" | "failed";

export interface PhoneCall {
  id: string;
  started_at: string;
  capture_started_at: string | null;
  ended_at: string | null;
  status: CallStatus;
  recording_enabled: boolean;
  recording_ready: boolean;
  duration_ms: number;
  sequence: number;
  transcript: CallTranscriptEntry[];
}

export type CallEvent =
  | { type: "transcript"; sequence: number; entry: CallTranscriptEntry }
  | { type: "call"; sequence: number; status: CallStatus }
  | { type: "error"; message: string };

export interface Agent {
  id: string;
  slug: string;
  name: string;
  description: string;
}

export interface AgentThreadSummary {
  id: string;
  title: string;
  pinned: boolean;
  automation_id?: string;
}

export interface AgentAttachment {
  file_id: string;
}

export interface AgentMessageRequest {
  thread_id: string;
  message: string;
  attachments?: AgentAttachment[];
}

export interface AgentStreamRequest extends AgentMessageRequest {
  client_operation_id?: string;
}

export type AgentSyncRequest =
  | AgentMessageRequest
  | {
      // Omit thread_id for one-off work: the agent answers on a fresh
      // ephemeral thread that never appears in the user's thread list, and
      // returns its ID. Uploads are bound to the thread they were uploaded
      // to, so one-off sends are text-only.
      thread_id?: undefined;
      message: string;
      attachments?: never;
    };

export interface AgentSyncResponse {
  thread_id: string;
  response: string;
}

export interface AgentUpload {
  file_id: string;
  name: string;
  mime: string;
  size: number;
}

export interface AgentApprovalRequest {
  type: "approval_request";
  interrupt_id: string;
  action_index: number;
  tool: string;
  args: Record<string, unknown>;
  description: string;
  allowed_decisions: AgentResumeDecision["decision"][];
}

export interface AgentTextEvent {
  type: "text";
  content: string;
}

export interface AgentToolEvent {
  type: "tool";
  id: string;
  name: string;
  status: "ok" | "error";
  result?: unknown;
  error?: string;
}

// A reloaded thread replays the same text and tool events the live stream
// emits, so one renderer handles both history and streaming. Unanswered
// approvals come back through `pending_approvals`, not as message events.
export type AgentMessageEvent = AgentTextEvent | AgentToolEvent;

export interface AgentThreadMessage {
  id: string;
  role: "user" | "assistant";
  events: AgentMessageEvent[];
  attachments?: AgentThreadAttachment[];
}

// User uploads and agent-generated files on a reloaded thread. fileId is the
// file's ID in listFiles and fileURL.
export interface AgentThreadAttachment {
  fileId: string;
  name: string;
  mime: string;
  size: number;
}

// A file in a thread: a user's upload or a file the agent generated.
export interface AgentThreadFile {
  id: string;
  name: string;
  size: number;
  content_type: string;
  created_at: string;
  kind: "uploaded" | "generated";
}

export interface AgentThread {
  id: string;
  title: string;
  messages: AgentThreadMessage[];
  pending_approvals: AgentApprovalRequest[];
  streaming: boolean;
}

export interface AgentResumeDecision {
  interrupt_id: string;
  action_index: number;
  decision: "approve" | "edit" | "reject";
  args_override?: Record<string, unknown>;
  message?: string;
}

export type AgentStreamEvent = Record<string, unknown>;

export class AgentClientError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "AgentClientError";
    this.status = status;
  }
}

async function errorMessage(response: Response): Promise<string> {
  const body = await response.text();
  if (!body) {
    return `agent request failed with status ${response.status}`;
  }
  try {
    const parsed = JSON.parse(body) as { detail?: unknown };
    if (typeof parsed.detail === "string" && parsed.detail) {
      return parsed.detail;
    }
  } catch {
    return body;
  }
  return body;
}

async function send(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<Response> {
  return reloadOnSignedOut(input, await fetch(input, init));
}

async function requireOK(response: Response): Promise<Response> {
  if (!response.ok) {
    throw new AgentClientError(response.status, await errorMessage(response));
  }
  return response;
}

async function requestJSON<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await requireOK(
    await send(path, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
    }),
  );
  return (await response.json()) as T;
}

function agentPath(agentIdentifier: string): string {
  const identifier = agentIdentifier.trim();
  if (!identifier) {
    throw new Error("agent identifier is required");
  }
  return `/api/_atlas/agents/${encodeURIComponent(identifier)}`;
}

async function* parseSSE<Event = AgentStreamEvent>(response: Response): AsyncGenerator<Event> {
  if (!response.body) {
    throw new AgentClientError(response.status, "agent stream has no response body");
  }

  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  try {
    while (true) {
      const { done, value } = await reader.read();
      buffer += value ?? "";
      let boundary = buffer.search(/\r?\n\r?\n/);
      while (boundary >= 0) {
        const frame = buffer.slice(0, boundary);
        const separator = buffer.slice(boundary).match(/^\r?\n\r?\n/)?.[0] ?? "\n\n";
        buffer = buffer.slice(boundary + separator.length);
        const data = frame
          .split(/\r?\n/)
          .filter((line) => line.startsWith("data:"))
          .map((line) => line.slice(5).trimStart())
          .join("\n");
        if (data) {
          yield JSON.parse(data) as Event;
        }
        boundary = buffer.search(/\r?\n\r?\n/);
      }
      if (done) {
        break;
      }
    }
    if (buffer.trim()) {
      const data = buffer
        .split(/\r?\n/)
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).trimStart())
        .join("\n");
      if (data) {
        yield JSON.parse(data) as Event;
      }
    }
  } finally {
    try {
      await reader.cancel();
    } finally {
      reader.releaseLock();
    }
  }
}

export async function listAgents(): Promise<Agent[]> {
  return requestJSON<Agent[]>("/api/_atlas/agents");
}

export async function getPairedAgent(): Promise<Agent> {
  return requestJSON<Agent>("/api/_atlas/agents/paired");
}

export class AgentClient {
  readonly identifier: string;
  readonly basePath: string;

  constructor(agentIdentifier: string) {
    this.identifier = agentIdentifier.trim();
    this.basePath = agentPath(this.identifier);
  }

  async getCall(access: CallAccess): Promise<PhoneCall> {
    return requestJSON<PhoneCall>(`${this.basePath}/calls/${encodeURIComponent(access.id)}`, {
      method: "POST", body: JSON.stringify({ token: access.token }),
    });
  }

  async *subscribeCall(
    access: CallAccess,
    options?: { after?: number; signal?: AbortSignal },
  ): AsyncGenerator<CallEvent> {
    const response = await requireOK(await send(
      `${this.basePath}/calls/${encodeURIComponent(access.id)}/events`,
      {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: access.token, after: options?.after ?? 0 }),
        signal: options?.signal,
      },
    ));
    yield* parseSSE<CallEvent>(response);
  }

  async callRecording(access: CallAccess): Promise<Blob> {
    const response = await requireOK(await send(
      `${this.basePath}/calls/${encodeURIComponent(access.id)}/recording`,
      {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: access.token }),
      },
    ));
    return response.blob();
  }

  async deleteCall(access: CallAccess): Promise<void> {
    await requireOK(await send(`${this.basePath}/calls/${encodeURIComponent(access.id)}/delete`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: access.token }),
    }));
  }

  async listThreads(limit = 50): Promise<AgentThreadSummary[]> {
    const query = new URLSearchParams({ limit: String(limit) });
    return requestJSON<AgentThreadSummary[]>(
      `${this.basePath}/threads?${query.toString()}`,
    );
  }

  async createThread(
    message?: string,
    options?: { ephemeral?: boolean; threadID?: string },
  ): Promise<{ id: string; title: string }> {
    const body: {
      thread_id: string;
      message?: string;
      ephemeral?: boolean;
    } = { thread_id: options?.threadID ?? crypto.randomUUID() };
    if (message) {
      body.message = message;
    }
    if (options?.ephemeral) {
      body.ephemeral = true;
    }
    return requestJSON<{ id: string; title: string }>(`${this.basePath}/threads`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  async getThread(threadID: string): Promise<AgentThread> {
    return requestJSON<AgentThread>(
      `${this.basePath}/threads/${encodeURIComponent(threadID)}`,
    );
  }

  async renameThread(
    threadID: string,
    title: string,
  ): Promise<{ id: string; title: string }> {
    return requestJSON<{ id: string; title: string }>(
      `${this.basePath}/threads/${encodeURIComponent(threadID)}`,
      { method: "PATCH", body: JSON.stringify({ title }) },
    );
  }

  async deleteThread(threadID: string): Promise<{ ok: boolean }> {
    return requestJSON<{ ok: boolean }>(
      `${this.basePath}/threads/${encodeURIComponent(threadID)}`,
      { method: "DELETE" },
    );
  }

  async pinThread(threadID: string, pinned: boolean): Promise<{ ok: boolean }> {
    return requestJSON<{ ok: boolean }>(
      `${this.basePath}/threads/${encodeURIComponent(threadID)}/pin`,
      { method: pinned ? "POST" : "DELETE" },
    );
  }

  async upload(
    threadID: string,
    file: File,
    fileName = file.name,
    fileID = crypto.randomUUID(),
  ): Promise<AgentUpload> {
    const body = new FormData();
    body.append("file", file);
    body.append("file_name", fileName);
    body.append("file_id", fileID);
    const response = await requireOK(
      await send(
        `${this.basePath}/threads/${encodeURIComponent(threadID)}/uploads`,
        { method: "POST", body },
      ),
    );
    return (await response.json()) as AgentUpload;
  }

  async listFiles(threadID: string): Promise<AgentThreadFile[]> {
    return requestJSON<AgentThreadFile[]>(
      `${this.basePath}/threads/${encodeURIComponent(threadID)}/files`,
    );
  }

  fileURL(threadID: string, fileID: string): string {
    return `${this.basePath}/threads/${encodeURIComponent(threadID)}/files/${encodeURIComponent(fileID)}/content`;
  }

  async send(message: AgentSyncRequest): Promise<AgentSyncResponse> {
    return requestJSON<AgentSyncResponse>(`${this.basePath}/chat`, {
      method: "POST",
      body: JSON.stringify(message),
    });
  }

  async *stream(
    message: AgentStreamRequest,
  ): AsyncGenerator<AgentStreamEvent> {
    const response = await requireOK(
      await send(`${this.basePath}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...message,
          client_operation_id:
            message.client_operation_id ?? crypto.randomUUID(),
        }),
      }),
    );
    if (response.status === 204) {
      return;
    }
    yield* parseSSE(response);
  }

  async *resume(
    threadID: string,
    decisions: AgentResumeDecision[],
  ): AsyncGenerator<AgentStreamEvent> {
    const response = await requireOK(
      await send(`${this.basePath}/chat/resume`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ thread_id: threadID, decisions }),
      }),
    );
    yield* parseSSE(response);
  }

  async *attach(threadID: string): AsyncGenerator<AgentStreamEvent> {
    const response = await send(`${this.basePath}/chat/attach`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ thread_id: threadID }),
    });
    if (response.status === 204) {
      return;
    }
    yield* parseSSE(await requireOK(response));
  }

  async stop(
    threadID: string,
  ): Promise<{ ok: boolean; stopped: boolean }> {
    return requestJSON<{ ok: boolean; stopped: boolean }>(
      `${this.basePath}/chat/stop`,
      {
        method: "POST",
        body: JSON.stringify({ thread_id: threadID }),
      },
    );
  }
}
