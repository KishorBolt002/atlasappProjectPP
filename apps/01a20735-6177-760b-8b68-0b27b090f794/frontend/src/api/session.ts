// A 401 usually means the sign-in in front of this page has ended, and only a
// page load renews it, so the page reloads. Paths that already caused a reload
// are kept for the tab until they succeed again: a credential a reload cannot
// renew then surfaces as the normal error instead of reloading forever. The
// calls already in flight when a session ends all get the same 401 and must
// not each restart the page.
const RELOADED_PATHS_KEY = "session-reload-paths";
let reloading = false;

function reloadedPaths(): string[] {
  const stored = sessionStorage.getItem(RELOADED_PATHS_KEY);
  if (!stored) {
    return [];
  }
  const paths: string[] = JSON.parse(stored);
  return paths;
}

function saveReloadedPaths(paths: string[]): void {
  if (paths.length) {
    sessionStorage.setItem(RELOADED_PATHS_KEY, JSON.stringify(paths));
  } else {
    sessionStorage.removeItem(RELOADED_PATHS_KEY);
  }
}

export function reloadOnSignedOut(
  request: RequestInfo | URL,
  response: Response,
): Response {
  // Outside a page, such as in a worker or a test without a DOM, there is no
  // page to reload.
  if (typeof window === "undefined") {
    return response;
  }
  const target = request instanceof Request ? request.url : String(request);
  const path = new URL(target, window.location.href).pathname;
  const paths = reloadedPaths();
  if (response.ok) {
    if (paths.includes(path)) {
      saveReloadedPaths(paths.filter((reloaded) => reloaded !== path));
    }
    return response;
  }
  if (response.status === 401 && !reloading && !paths.includes(path)) {
    reloading = true;
    saveReloadedPaths([...paths, path]);
    window.location.reload();
  }
  return response;
}
