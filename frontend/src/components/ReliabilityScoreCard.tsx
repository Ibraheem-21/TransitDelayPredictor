import { ShieldCheck } from 'lucide-react'
import type { Reliability } from '../types/transit'

const gradeColor: Record<string, string> = {
  High: 'text-emerald-700',
  Medium: 'text-amber-700',
  Low: 'text-red-700',
  Unknown: 'text-slate-500',
}

const barColor: Record<string, string> = {
  High: 'bg-emerald-600',
  Medium: 'bg-amber-500',
  Low: 'bg-red-500',
  Unknown: 'bg-slate-300',
}

export function ReliabilityScoreCard({ reliability }: { reliability: Reliability | null }) {
  const score = reliability?.score ?? null
  const grade = reliability?.grade ?? 'Unknown'
  const components = reliability?.components

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-5 w-5 text-emerald-700" />
          <h2 className="text-base font-semibold">Reliability</h2>
        </div>
        <span className={`rounded-md bg-slate-50 px-2 py-1 text-xs font-semibold ${gradeColor[grade]}`}>{grade}</span>
      </div>

      <div className="flex items-end gap-2">
        <p className={`text-5xl font-semibold ${gradeColor[grade]}`}>{score ?? '—'}</p>
        {score != null && <p className="pb-1.5 text-sm text-slate-500">/ 100</p>}
      </div>

      <div className="mt-3 h-2 rounded-full bg-slate-100">
        <div
          className={`h-2 rounded-full ${barColor[grade]}`}
          style={{ width: `${Math.max(0, Math.min(100, score ?? 0))}%` }}
        />
      </div>

      {reliability?.reasons?.length ? (
        <ul className="mt-4 space-y-1.5 text-sm text-slate-600">
          {reliability.reasons.map((reason) => (
            <li key={reason} className="flex gap-2">
              <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-300" />
              <span>{reason}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-4 text-sm text-slate-500">Select a route to see its reliability breakdown.</p>
      )}

      {components && components.sample_size > 0 && (
        <p className="mt-3 text-xs text-slate-400">
          Based on {components.sample_size} observations · {components.delay_frequency_pct}% delayed ·{' '}
          {components.avg_delay_minutes} min avg
        </p>
      )}
    </div>
  )
}
