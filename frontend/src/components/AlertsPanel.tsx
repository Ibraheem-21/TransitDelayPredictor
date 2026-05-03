import type { Alert } from '../types/transit'

export function AlertsPanel({ alerts }: { alerts: Alert[] }) {
  if (alerts.length === 0) {
    return <p className="rounded-md bg-slate-50 p-3 text-sm text-slate-600">No active alerts for this route.</p>
  }

  return (
    <div className="max-h-44 space-y-2 overflow-auto pr-1">
      {alerts.map((alert) => (
        <article key={alert.id} className="rounded-md border border-amber-200 bg-amber-50 p-3">
          <h3 className="text-sm font-semibold text-amber-950">{alert.alert_header ?? 'Service alert'}</h3>
          <p className="mt-1 line-clamp-2 text-sm text-amber-900">{alert.alert_description ?? 'Details unavailable.'}</p>
        </article>
      ))}
    </div>
  )
}
