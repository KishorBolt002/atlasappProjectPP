// Agent embed widget — feature parity with floating-agent-widget.tsx
// Constants match the React component exactly
// Customer host integrations are specific to this app-owned wrapper.
window.atlasAgentWidget = function (opts) {
  var DEFAULT_ACCENT = "#0284c7";
  var DEFAULT_ACCENT_FG = "#ffffff";

  var agentId = typeof opts.agentId === "string" ? opts.agentId.trim() : "";
  // The ID the app's code names this agent by, which differs from agentId in a
  // project copied with its agents; selections are reported to the app under it.
  var appAgentId = typeof opts.appAgentId === "string" ? opts.appAgentId.trim() : "";
  var agentName = opts.agentName;
  var frameUrl = opts.frameUrl;
  var accent = opts.accent === undefined ? DEFAULT_ACCENT : opts.accent;
  var accentFg = opts.accentFg === undefined ? DEFAULT_ACCENT_FG : opts.accentFg;

  var DEFAULT_WIDTH = 480;
  var DEFAULT_HEIGHT = 600;
  var MIN_WIDTH = 360;
  var MAX_WIDTH = 720;
  var MIN_HEIGHT = 320;
  var EDGE_MARGIN = 16;
  var ROOT_ID = "atlas-agent-embed-root";

  if (!agentId) throw new Error("atlasAgentWidget requires agentId");
  if (!appAgentId) throw new Error("atlasAgentWidget requires appAgentId");
  if (document.getElementById(ROOT_ID)) return;

  var frameOrigin = new URL(frameUrl, window.location.href).origin;

  var isDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;

  function getThemeVars(dark) {
    return {
      "--accent": accent,
      "--accent-fg": accentFg,
      "--surface": dark ? "#1e293b" : "#ffffff",
      "--fg": dark ? "#e2e8f0" : "#0f172a",
      "--fg-muted": dark ? "#94a3b8" : "#64748b",
      "--border": dark ? "rgba(255,255,255,0.1)" : "rgba(15,23,42,0.12)",
      "--muted": dark ? "rgba(255,255,255,0.06)" : "rgba(15,23,42,0.06)",
      "--frame-bg": dark ? "#0f172a" : "#f1f5f9",
      "--shadow": dark ? "0 4px 12px rgba(0,0,0,0.2), 0 2px 4px rgba(0,0,0,0.1)" : "0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04)",
    };
  }

  function escapeHtml(value) {
    return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#39;");
  }

  function clampToRange(value, min, max) {
    if (max <= min) return max;
    return Math.min(max, Math.max(min, value));
  }

  // Icons (matching lucide)
  var ICON_BOT = '<svg viewBox="0 0 24 24" fill="none"><path d="M12 8V4H8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><rect width="16" height="12" x="4" y="8" rx="2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M2 14h2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M20 14h2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M15 13v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M9 13v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  var ICON_EXTERNAL = '<svg viewBox="0 0 24 24" fill="none"><path d="M22 12A10 10 0 1 1 12 2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M22 2 12 12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M16 2h6v6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  var ICON_CHEVRON_DOWN = '<svg viewBox="0 0 24 24" fill="none"><path d="M6 9l6 6 6-6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';

  var initialLeft = document.documentElement.clientWidth - 56 - EDGE_MARGIN;
  var host = document.createElement("div");
  host.id = ROOT_ID;
  host.style.cssText = "position:fixed; bottom:16px; left:" + initialLeft + "px; z-index:2147483000; display:none; transition:left 150ms ease";
  var sr = host.attachShadow({ mode: "open" });
  var styleEl = document.createElement("style");
  fetch("/agent-embed-styles.css").then(function (r) { return r.text(); }).then(function (css) {
    styleEl.textContent = css;
    host.style.display = "block";
  });
  sr.appendChild(styleEl);

  // Apply theme
  function applyTheme(dark) {
    var vars = getThemeVars(dark);
    for (var key in vars) host.style.setProperty(key, vars[key]);
  }
  applyTheme(isDark);

  if (window.matchMedia) {
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function (e) {
      isDark = e.matches;
      applyTheme(isDark);
    });
  }

  // Build DOM
  var safeName = escapeHtml(agentName);
  var shell = document.createElement("div");
  shell.className = "shell";
  shell.dataset.open = "false";
  shell.innerHTML =
    '<div style="position:relative; display:none">'
    + '<section class="panel">'
    + '<header class="header">'
    + '<div class="header-left"><span class="header-icon">' + ICON_BOT + '</span><span class="title">' + safeName + '</span></div>'
    + '<div class="header-actions">'
    + '<button class="icon-btn open-tab" type="button" aria-label="Open in new tab">' + ICON_EXTERNAL + '</button>'
    + '<button class="icon-btn minimize" type="button" aria-label="Minimize">' + ICON_CHEVRON_DOWN + '</button>'
    + '</div></header>'
    // Microphone is delegated so agent voice conversations work inside the
    // cross-origin widget frame.
    + '<div class="body"><iframe title="' + safeName + '" allow="clipboard-write; microphone"></iframe></div>'
    + '</section>'
    + '<div class="resize-top"></div><div class="resize-left"></div><div class="resize-right"></div>'
    + '<div class="resize-top-left"></div><div class="resize-top-right"></div>'
    + '</div>'
    + '<button class="fab" type="button" aria-expanded="false" aria-label="Open assistant">' + ICON_BOT + '</button>';
  sr.appendChild(shell);

  var panelWrapper = shell.firstElementChild; // the relative div wrapping panel + resize handles
  var panel = sr.querySelector(".panel");
  var header = sr.querySelector(".header");
  var fab = sr.querySelector(".fab");
  var minimizeBtn = sr.querySelector(".minimize");
  var openTabBtn = sr.querySelector(".open-tab");
  var iframe = sr.querySelector("iframe");

  document.body.appendChild(host);

  // State
  var isOpen = false;
  var hasLoadedFrame = false;
  var widgetWidth = DEFAULT_WIDTH;
  var widgetHeight = DEFAULT_HEIGHT;
  var leftOffset = initialLeft;
  var positionRatio = 1;
  var dragState = null;
  var resizeState = null;
  var dragCleanup = null;
  var resizeCleanup = null;

  function sync() {
    if (isOpen) {
      panelWrapper.style.display = "block";
      panel.style.width = widgetWidth + "px";
      panel.style.height = widgetHeight + "px";
      fab.style.display = "none";
      if (!hasLoadedFrame) {
        iframe.setAttribute("src", frameUrl);
        hasLoadedFrame = true;
      }
    } else {
      panelWrapper.style.display = "none";
      fab.style.display = "";
    }
  }

  function openPanel() {
    if (isOpen) return;
    // Reposition: panel right edge aligns with FAB right edge
    var fabRight = leftOffset + 56;
    leftOffset = Math.max(EDGE_MARGIN, fabRight - widgetWidth);
    host.style.left = leftOffset + "px";
    isOpen = true;
    sync();
  }

  function closePanel() {
    if (!isOpen) return;
    // Reposition: FAB right edge aligns with panel right edge
    var panelRight = leftOffset + widgetWidth;
    var bounds = getBounds(56);
    if (bounds) {
      leftOffset = clampToRange(panelRight - 56, bounds.minLeft, bounds.maxLeft);
    }
    host.style.left = leftOffset + "px";
    isOpen = false;
    sync();
  }

  function getBounds(containerWidth) {
    var parent = host.parentElement;
    if (!parent) return null;
    var parentRect = parent.getBoundingClientRect();
    var minLeft = EDGE_MARGIN;
    var maxLeft = Math.max(minLeft, parentRect.width - containerWidth - EDGE_MARGIN);
    return { minLeft: minLeft, maxLeft: maxLeft, range: maxLeft - minLeft };
  }

  // Drag logic — ported from floating-agent-widget.tsx
  function startDrag(event, source) {
    if (!event.isPrimary) return;
    if (event.pointerType === "mouse" && event.button !== 0) return;
    var parent = host.parentElement;
    if (!parent) return;

    if (resizeCleanup) { resizeCleanup(); resizeCleanup = null; }
    resizeState = null;

    if (dragCleanup) { dragCleanup(); dragCleanup = null; }

    var hostRect = host.getBoundingClientRect();
    var parentRect = parent.getBoundingClientRect();
    var width = source === "header" ? widgetWidth : hostRect.width;
    if (width <= 0) return;
    var bounds = getBounds(width);
    if (!bounds) return;
    var rawLeft = leftOffset !== null ? leftOffset : hostRect.left - parentRect.left;
    var currentLeft = clampToRange(rawLeft, bounds.minLeft, bounds.maxLeft);

    event.currentTarget.setPointerCapture(event.pointerId);
    dragState = {
      startX: event.clientX, startLeft: currentLeft,
      minLeft: bounds.minLeft, maxLeft: bounds.maxLeft, range: bounds.range,
      hasMoved: false, source: source, pointerId: event.pointerId, target: event.currentTarget,
    };
    leftOffset = currentLeft;
    positionRatio = bounds.range === 0 ? 0 : (currentLeft - bounds.minLeft) / bounds.range;
    host.style.left = leftOffset + "px";

    var suppressClick = false;

    function onMove(e) {
      if (!dragState || dragState.pointerId !== e.pointerId) return;
      var dx = e.clientX - dragState.startX;
      if (!dragState.hasMoved) {
        if (Math.abs(dx) <= 3) return;
        dragState.hasMoved = true;
        header.dataset.dragging = "true";
        host.style.transition = "none";
      }
      var nextLeft = clampToRange(dragState.startLeft + dx, dragState.minLeft, dragState.maxLeft);
      positionRatio = dragState.range === 0 ? 0 : (nextLeft - dragState.minLeft) / dragState.range;
      leftOffset = nextLeft;
      host.style.left = nextLeft + "px";
    }
    function onEnd(e) {
      if (!dragState || dragState.pointerId !== e.pointerId) return;
      if (dragState.source === "fab" && dragState.hasMoved) suppressClick = true;
      if (dragState.target && dragState.target.hasPointerCapture && dragState.target.hasPointerCapture(dragState.pointerId)) {
        dragState.target.releasePointerCapture(dragState.pointerId);
      }
      header.dataset.dragging = "false";
      host.style.transition = "left 150ms ease";
      dragState = null;
      cleanup();
    }
    function cleanup() {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onEnd);
      window.removeEventListener("pointercancel", onEnd);
      dragCleanup = null;
    }
    dragCleanup = cleanup;
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onEnd);
    window.addEventListener("pointercancel", onEnd);

    // Return suppressClick checker for FAB
    return function () { var v = suppressClick; suppressClick = false; return v; };
  }

  // Resize logic — ported from floating-agent-widget.tsx
  function startResize(event, direction) {
    if (!isOpen || !event.isPrimary) return;
    if (event.pointerType === "mouse" && event.button !== 0) return;
    var parent = host.parentElement;
    if (!parent) return;
    host.style.transition = "none";

    if (dragCleanup) { dragCleanup(); dragCleanup = null; }
    dragState = null;
    if (resizeCleanup) { resizeCleanup(); resizeCleanup = null; }

    var hostRect = host.getBoundingClientRect();
    var parentRect = parent.getBoundingClientRect();
    var bounds = getBounds(widgetWidth);
    if (!bounds) return;
    var rawLeft = leftOffset !== null ? leftOffset : hostRect.left - parentRect.left;
    var sLeft = clampToRange(rawLeft, bounds.minLeft, bounds.maxLeft);
    var maxW = Math.max(0, Math.min(MAX_WIDTH, parentRect.width - EDGE_MARGIN * 2));
    var maxH = Math.max(0, parentRect.height - EDGE_MARGIN * 2);

    event.currentTarget.setPointerCapture(event.pointerId);
    resizeState = {
      startX: event.clientX, startY: event.clientY,
      startLeft: sLeft, startWidth: widgetWidth, startHeight: widgetHeight,
      startRight: sLeft + widgetWidth, parentWidth: parentRect.width,
      maxWidth: maxW, maxHeight: maxH, direction: direction,
      pointerId: event.pointerId, target: event.currentTarget,
    };

    // Add overlay to prevent iframe capture
    var overlay = document.createElement("div");
    overlay.className = "drag-overlay";
    panel.appendChild(overlay);

    function onMove(e) {
      if (!resizeState || resizeState.pointerId !== e.pointerId) return;
      var dx = e.clientX - resizeState.startX;
      var dy = e.clientY - resizeState.startY;
      var nw = resizeState.startWidth;
      var nh = resizeState.startHeight;
      var nl = resizeState.startLeft;
      var incLeft = direction === "left" || direction === "top-left";
      var incRight = direction === "right" || direction === "top-right";
      var incTop = direction === "top" || direction === "top-left" || direction === "top-right";

      if (incLeft) {
        var maxWL = Math.max(0, Math.min(resizeState.maxWidth, resizeState.startRight - EDGE_MARGIN));
        var minW = Math.min(MIN_WIDTH, maxWL);
        nw = clampToRange(resizeState.startWidth - dx, minW, maxWL);
        nl = resizeState.startRight - nw;
      } else if (incRight) {
        var maxWR = Math.max(0, Math.min(resizeState.maxWidth, resizeState.parentWidth - resizeState.startLeft - EDGE_MARGIN));
        var minWR = Math.min(MIN_WIDTH, maxWR);
        nw = clampToRange(resizeState.startWidth + dx, minWR, maxWR);
        nl = resizeState.startLeft;
      }
      if (incTop) {
        var minH = Math.min(MIN_HEIGHT, resizeState.maxHeight);
        nh = clampToRange(resizeState.startHeight - dy, minH, resizeState.maxHeight);
      }

      var nb = getBounds(nw);
      if (nb) {
        nl = clampToRange(nl, nb.minLeft, nb.maxLeft);
        positionRatio = nb.range === 0 ? 0 : (nl - nb.minLeft) / nb.range;
      }
      widgetWidth = nw;
      widgetHeight = nh;
      leftOffset = nl;
      host.style.left = nl + "px";
      sync();
    }
    function onEnd(e) {
      if (!resizeState || resizeState.pointerId !== e.pointerId) return;
      if (resizeState.target && resizeState.target.hasPointerCapture && resizeState.target.hasPointerCapture(resizeState.pointerId)) {
        resizeState.target.releasePointerCapture(resizeState.pointerId);
      }
      resizeState = null;
      host.style.transition = "left 150ms ease";
      if (overlay.parentNode) overlay.remove();
      cleanup();
    }
    function cleanup() {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onEnd);
      window.removeEventListener("pointercancel", onEnd);
      resizeCleanup = null;
    }
    resizeCleanup = cleanup;
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onEnd);
    window.addEventListener("pointercancel", onEnd);
  }

  // Wire events
  var fabSuppressCheck = null;
  fab.addEventListener("pointerdown", function (e) { fabSuppressCheck = startDrag(e, "fab"); });
  fab.addEventListener("click", function (e) {
    if (fabSuppressCheck && fabSuppressCheck()) { e.preventDefault(); return; }
    openPanel();
  });
  header.addEventListener("pointerdown", function (e) {
    if (e.target.closest(".header-actions")) return;
    startDrag(e, "header");
  });
  minimizeBtn.addEventListener("click", function () { closePanel(); });
  openTabBtn.addEventListener("click", function () { window.open(frameUrl, "_blank", "noopener,noreferrer"); });
  window.addEventListener("keydown", function (e) { if (e.key === "Escape" && isOpen) { closePanel(); } });
  iframe.addEventListener("load", function () {
    if (!iframe.contentWindow) return;
    iframe.contentWindow.postMessage({ type: "atlas-agent-parent-origin", agentId: agentId }, frameOrigin);
  });
  window.addEventListener("message", function (event) {
    if (event.source !== iframe.contentWindow || event.origin !== frameOrigin) return;
    if (!event.data || event.data.type !== "atlas-agent-thread-selected" || event.data.agentId !== agentId || typeof event.data.threadId !== "string") return;

    var threadId = event.data.threadId;
    window.dispatchEvent(new CustomEvent("atlas-agent-thread-selected", { detail: { agentId: appAgentId, threadId: threadId } }));
  });

  // Resize handles
  sr.querySelector(".resize-top").addEventListener("pointerdown", function (e) { startResize(e, "top"); });
  sr.querySelector(".resize-left").addEventListener("pointerdown", function (e) { startResize(e, "left"); });
  sr.querySelector(".resize-right").addEventListener("pointerdown", function (e) { startResize(e, "right"); });
  sr.querySelector(".resize-top-left").addEventListener("pointerdown", function (e) { startResize(e, "top-left"); });
  sr.querySelector(".resize-top-right").addEventListener("pointerdown", function (e) { startResize(e, "top-right"); });

  // Reposition on window resize
  var resizeObserver = new ResizeObserver(function () {
    if (dragState || resizeState) return;
    var parent = host.parentElement;
    if (!parent) return;
    var parentRect = parent.getBoundingClientRect();
    if (isOpen) {
      var maxW = Math.max(0, Math.min(MAX_WIDTH, parentRect.width - EDGE_MARGIN * 2));
      var minW = Math.min(MIN_WIDTH, maxW);
      widgetWidth = clampToRange(widgetWidth, minW, maxW);
      var maxH = Math.max(0, parentRect.height - EDGE_MARGIN * 2);
      var minH = Math.min(MIN_HEIGHT, maxH);
      widgetHeight = clampToRange(widgetHeight, minH, maxH);
    }
    var w = isOpen ? widgetWidth : 56;
    var bounds = getBounds(w);
    if (!bounds) return;
    var nextLeft = bounds.minLeft + bounds.range * positionRatio;
    leftOffset = clampToRange(nextLeft, bounds.minLeft, bounds.maxLeft);
    host.style.left = leftOffset + "px";
    sync();
  });
  resizeObserver.observe(document.body);

  sync();
};
