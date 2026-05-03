import type { Route } from '../types/transit'

export type RouteMode = 'rail' | 'bus'

type Props = {
  routes: Route[]
  mode: RouteMode
  onModeChange: (value: RouteMode) => void
  value: string
  onChange: (value: string) => void
}

export function RouteSelector({ routes, mode, onModeChange, value, onChange }: Props) {
  const railCount = routes.filter((route) => route.route_type === '2').length
  const busCount = routes.filter((route) => route.route_type !== '2').length
  const visibleRoutes = routes.filter((route) => (mode === 'rail' ? route.route_type === '2' : route.route_type !== '2'))

  return (
    <div className="grid gap-3 text-sm">
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center justify-between gap-3">
          <span className="font-medium text-slate-700">Route type</span>
          <span className="rounded bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
            {mode === 'rail' ? `${railCount} rail` : `${busCount} bus`}
          </span>
        </div>
        <div className="grid grid-cols-2 rounded-md border border-slate-300 bg-slate-100 p-1">
          <ModeButton active={mode === 'rail'} onClick={() => onModeChange('rail')} label="Rail" />
          <ModeButton active={mode === 'bus'} onClick={() => onModeChange('bus')} label="Bus" />
        </div>
      </div>

      <label className="flex flex-col gap-1.5">
        <span className="font-medium text-slate-700">Route</span>
        <select
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="min-h-11 rounded-md border border-slate-300 bg-white px-3 text-slate-950 outline-none transition focus:border-emerald-700 focus:ring-2 focus:ring-emerald-100"
        >
          <option value="">Choose {mode} route</option>
          {visibleRoutes.map((route) => (
            <option key={route.route_id} value={route.route_id}>
              {route.route_name}
            </option>
          ))}
        </select>
      </label>
    </div>
  )
}

function ModeButton({ active, onClick, label }: { active: boolean; onClick: () => void; label: string }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`min-h-9 rounded px-3 text-sm font-semibold transition ${
        active ? 'bg-white text-emerald-800 shadow-sm' : 'text-slate-600 hover:text-slate-900'
      }`}
    >
      {label}
    </button>
  )
}
