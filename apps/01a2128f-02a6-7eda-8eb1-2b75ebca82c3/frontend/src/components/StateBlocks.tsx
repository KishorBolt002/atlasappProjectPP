import { AlertTriangle, Loader2 } from 'lucide-react'

export function LoadingBlock({ label }: { label: string }) {
  return (
    <div
      role="status"
      className="flex items-center justify-center gap-2 px-4 py-8 text-sm text-slate-500"
    >
      <Loader2 className="size-4 animate-spin text-blue-600" />
      {label}
    </div>
  )
}

export function ErrorBlock({
  title,
  message,
  onRetry,
}: {
  title: string
  message: string
  onRetry?: () => void
}) {
  return (
    <div
      role="alert"
      className="m-4 flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm"
    >
      <AlertTriangle className="mt-0.5 size-4 shrink-0 text-red-600" />
      <div className="flex-1">
        <p className="font-medium text-red-800">{title}</p>
        <p className="mt-0.5 break-words text-red-700">{message}</p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="rounded-md border border-red-200 bg-white px-2.5 py-1 text-xs font-medium text-red-700 hover:bg-red-100 focus-visible:outline-2 focus-visible:outline-red-600"
        >
          Retry
        </button>
      )}
    </div>
  )
}
