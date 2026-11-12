(function () {
  if (window.atlasAgentEmbedLoaded) return;
  window.atlasAgentEmbedLoaded = true;

  var CONFIG_PATH = "/_atlas/agent-embed-config.json";
  var HEX_PATTERN = /^#[0-9a-fA-F]{3,6}$/;
  var DEFAULT_ACCENT = "#0284c7";
  var DEFAULT_ACCENT_FG = "#ffffff";

  function readMetaHex(name) {
    var el = document.querySelector('meta[name="' + name + '"]');
    return el && HEX_PATTERN.test((el.content || "").trim()) ? el.content.trim() : "";
  }

  var accent = readMetaHex("atlas-agent-accent") || DEFAULT_ACCENT;
  var accentFg = readMetaHex("atlas-agent-accent-foreground") || DEFAULT_ACCENT_FG;
  var background = readMetaHex("atlas-agent-background");
  var foreground = readMetaHex("atlas-agent-foreground");

  // When in iframe (Build preview), post theme colors to parent and exit. The
  // preview hosts the assistant itself and relays the conversation it shows
  // here, so listeners on this window see the same event the widget dispatches.
  if (window.self !== window.top) {
    try {
      var origin = document.referrer ? new URL(document.referrer).origin : null;
      if (origin && window.parent) {
        window.parent.postMessage({ type: "atlas-agent-accent", accent: accent, foreground: accentFg, background: background, textColor: foreground }, origin);
        window.addEventListener("message", function (event) {
          if (event.source !== window.parent || event.origin !== origin) return;
          if (!event.data || event.data.type !== "atlas-agent-thread-selected" || typeof event.data.agentId !== "string" || typeof event.data.threadId !== "string") return;
          window.dispatchEvent(new CustomEvent("atlas-agent-thread-selected", { detail: { agentId: event.data.agentId, threadId: event.data.threadId } }));
        });
      }
    } catch (_e) {}
    return;
  }

  async function init() {
    var config = null;
    try {
      var response = await fetch(CONFIG_PATH, { credentials: "include", headers: { Accept: "application/json" } });
      if (response.ok && (response.headers.get("content-type") || "").includes("application/json")) {
        config = await response.json();
      }
    } catch (_e) {
      return;
    }

    if (!config || !config.enabled || !config.agent_id || !config.app_agent_id || !config.agent_url || !config.agent_token) return;

    var agentId = config.agent_id.trim();
    var appAgentId = config.app_agent_id.trim();
    var agentName = (config.agent_name || "Atlas Agent").trim();
    var agentUrl = config.agent_url.trim();
    var agentToken = (config.agent_token || "").trim();
    var frameUrl = agentToken ? new URL(agentUrl, window.location.href) : agentUrl;
    if (agentToken && typeof frameUrl === "object") {
      frameUrl.searchParams.set("token", agentToken);
      frameUrl = frameUrl.toString();
    }

    // Wait for the widget script to be available
    if (typeof window.atlasAgentWidget === "function") {
      window.atlasAgentWidget({ agentId: agentId, appAgentId: appAgentId, agentName: agentName, frameUrl: frameUrl, accent: accent, accentFg: accentFg, background: background, foreground: foreground });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    void init();
  }
})();
