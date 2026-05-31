import { Activity, TrendingUp } from 'lucide-react'
import type { PredictionResult } from '../types/transit'

const riskClasses: Record<string, string> = {
  Low: 'bg-emerald-100 text-emerald-800',
  Medium: 'bg-amber-100 text-amber-800',
  High: 'bg-red-100 text-red-800',
}

const liveStatusClasses: Record<string, string> = {
  'On time': 'bg-emerald-100 text-emerald-800',
  'Minor delays': 'bg-amber-100 text-amber-800',
  'Major delays': 'bg-red-100 text-red-800',
  'Cancellations reported': 'bg-red-100 text-red-800',
  'No live data': 'bg-slate-100 text-slate-600',
}

function formatTime(value?: string | null) {
  if (!value) return 'no recent data'
  return new Date(value).toLocaleString([], { hour: '2-digit', minute: '2-digit', month: 'short', day: 'numeric' })
}

export function PredictionCard({ prediction }: { prediction: PredictionResult | null }) {
  const probability = Math.round((prediction?.delay_probability ?? 0) * 100)
  const riskLabel = prediction?.risk_label ?? 'Low'
  const leaveEarly = Math.max(5, Math.round(prediction?.expected_delay_minutes ?? 5))
  const live = prediction?.live_status

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      {/* Live status: what is happening right now (observed) */}
      <div className="mb-4 rounded-md border border-slate-200 bg-slate-50 p-3">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-sky-700" />
            <h3 className="text-sm font-semibold text-slate-700">Live status</h3>
          </div>
          <span className={`rounded-md px-2 py-1 text-xs font-semibold ${liveStatusClasses[live?.status ?? 'No live data'] ?? 'bg-slate-100 text-slate-600'}`}>
            {live?.status ?? 'No live data'}
          </span>
        </div>
        <p className="mt-2 text-sm text-slate-600">
          {live && live.sample_size > 0
            ? `Currently ${live.average_delay_minutes} min average delay across ${live.sample_size} recent observations.`
            : 'No live trains observed in the last 90 minutes.'}
        </p>
        <p className="mt-1 text-xs text-slate-400">Updated {formatTime(live?.last_updated)}</p>
      </div>

      {/* Predicted risk: forecast for the chosen travel time */}
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-emerald-700" />
          <h2 className="text-base font-semibold">Predicted delay risk</h2>
        </div>
        <span className={`rounded-md px-2 py-1 text-xs font-semibold ${riskClasses[riskLabel]}`}>{riskLabel}</span>
      </div>
      <div className="space-y-3">
        <div>
          <p className="text-4xl font-semibold">{probability}%</p>
          <p className="text-sm text-slate-500">probability of a 5+ minute delay</p>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Stat label="Expected" value={`${prediction?.expected_delay_minutes ?? 0} min`} />
          <Stat label="Range" value={prediction?.delay_range ?? 'N/A'} />
        </div>
        <div className="rounded-md bg-slate-50 p-3 text-sm text-slate-700">
          <p className="font-medium">Recommendation</p>
          <p>Consider leaving {leaveEarly} minutes earlier.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {(prediction?.top_factors ?? ['waiting for route data']).map((factor) => (
            <span key={factor} className="rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-slate-600">
              {factor}
            </span>
          ))}
        </div>
        {prediction && (
          <p className="text-xs text-slate-400">
            {prediction.is_data_driven
              ? `Based on ${prediction.sample_size} collected observations · confidence ${prediction.confidence}`
              : 'Heuristic estimate — not enough history collected yet for this route.'}
          </p>
        )}
      </div>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-200 p-3">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <p className="mt-1 font-semibold">{value}</p>
    </div>
  )
}
