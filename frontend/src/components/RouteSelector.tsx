import { TrainFront } from 'lucide-react'
import type { Route } from '../types/transit'

type Props = {
  routes: Route[]
  value: string
  onChange: (value: string) => void
}

export function RouteSelector({ routes, value, onChange }: Props) {
  return (
    <div className="grid gap-3 text-sm">
      <div className="flex items-center justify-between gap-3">
        <span className="flex items-center gap-1.5 font-medium text-slate-700">
          <TrainFront className="h-4 w-4 text-emerald-700" />
          GO rail line
        </span>
        <span className="rounded bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
          {routes.length} lines
        </span>
      </div>

      <label className="flex flex-col gap-1.5">
        <span className="font-medium text-slate-700">Route</span>
        <select
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="min-h-11 rounded-md border border-slate-300 bg-white px-3 text-slate-950 outline-none transition focus:border-emerald-700 focus:ring-2 focus:ring-emerald-100"
        >
          <option value="">Choose a rail line</option>
          {routes.map((route) => (
            <option key={route.route_id} value={route.route_id}>
              {route.route_name}
            </option>
          ))}
        </select>
      </label>
    </div>
  )
}
