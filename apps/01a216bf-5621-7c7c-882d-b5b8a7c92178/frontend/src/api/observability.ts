interface Frame {
  asset: string;
  line: number;
  column: number;
}

function frameAt(file: string, row: number, col: number): Frame | null {
  if (!file.startsWith(`${window.location.origin}/`)) return null;
  const url = new URL(file);
  if (
    !url.pathname.endsWith(".js") &&
    !url.pathname.endsWith(".tsx") &&
    !url.pathname.endsWith(".ts")
  )
    return null;
  return { asset: url.pathname, line: row, column: col };
}

function errorType(error: unknown, defaultType: string): string {
  return error instanceof Error ? error.name : defaultType;
}

function report(event: string, type: string, frames: Frame[]): void {
  const body = JSON.stringify({ event, exception_type: type, frames });
  const payload = new Blob([body], { type: "application/json" });
  if (!navigator.sendBeacon("/api/_atlas/observability", payload)) {
    console.error("Observability browser event was not queued");
  }
}

function onError(event: ErrorEvent): void {
  const frame = frameAt(event.filename, event.lineno, event.colno);
  const type = errorType(event.error, "Error");
  report("browser.error", type, frame ? [frame] : []);
}

function onRejection(event: PromiseRejectionEvent): void {
  const frames: Frame[] = [];
  if (event.reason instanceof Error && event.reason.stack) {
    for (const line of event.reason.stack.split("\n").slice(1)) {
      const location = line.match(/(https?:\/\/[^\s)]+):(\d+):(\d+)\)?$/);
      if (location) {
        const [, filename, row, column] = location;
        const frame = frameAt(filename, Number(row), Number(column));
        if (frame) frames.push(frame);
      }
    }
  }
  const type = errorType(event.reason, "UnhandledRejection");
  report("browser.unhandled_rejection", type, frames);
}

window.addEventListener("error", onError);
window.addEventListener("unhandledrejection", onRejection);

if (import.meta.hot) {
  import.meta.hot.dispose(() => {
    window.removeEventListener("error", onError);
    window.removeEventListener("unhandledrejection", onRejection);
  });
}
