import type { Stop } from '../types/transit'

type Props = {
  stops: Stop[]
  value: string
  onChange: (value: string) => void
  disabled?: boolean
}

export function StopSelector({ stops, value, onChange, disabled }: Props) {
  return (
    <label className="flex flex-col gap-1.5 text-sm">
      <span className="font-medium text-slate-700">Stop or station</span>
      <select
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        className="min-h-11 rounded-md border border-slate-300 bg-white px-3 text-slate-950 outline-none transition focus:border-emerald-700 focus:ring-2 focus:ring-emerald-100 disabled:bg-slate-100"
      >
        <option value="">All stops</option>
        {stops.map((stop) => (
          <option key={stop.stop_id} value={stop.stop_id}>
            {stop.stop_name}
          </option>
        ))}
      </select>
    </label>
  )
}
