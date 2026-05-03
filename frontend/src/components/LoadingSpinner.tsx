import { Loader2 } from 'lucide-react'

export function LoadingSpinner() {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white p-3 text-sm text-slate-600 shadow-sm">
      <Loader2 className="h-4 w-4 animate-spin" />
      Loading transit data
    </div>
  )
}
