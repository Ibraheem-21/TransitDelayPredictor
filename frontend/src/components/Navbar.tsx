import { TrainFront } from 'lucide-react'

export function Navbar() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-emerald-700 text-white">
            <TrainFront className="h-5 w-5" />
          </div>
          <div>
            <p className="text-sm font-semibold leading-tight">GOPredict</p>
            <p className="text-xs text-slate-500">Schedule, realtime, weather</p>
          </div>
        </div>
      </div>
    </header>
  )
}
