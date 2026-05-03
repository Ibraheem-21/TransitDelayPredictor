import { AlertCircle } from 'lucide-react'

export function ErrorMessage({ message }: { message: string }) {
  return (
    <div className="mt-3 flex items-center gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800">
      <AlertCircle className="h-4 w-4" />
      {message}
    </div>
  )
}
