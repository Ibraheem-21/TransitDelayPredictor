import { TrendingUp } from 'lucide-react'
import type { PredictionResult } from '../types/transit'

type Props = {
  prediction: PredictionResult | null
  riskLabel: string
}

const riskClasses: Record<string, string> = {
  Low: 'bg-emerald-100 text-emerald-800',
  Medium: 'bg-amber-100 text-amber-800',
  High: 'bg-red-100 text-red-800',
}

export function PredictionCard({ prediction, riskLabel }: Props) {
  const probability = Math.round((prediction?.delay_probability ?? 0) * 100)
  const leaveEarly = Math.max(5, Math.round(prediction?.expected_delay_minutes ?? 5))

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-emerald-700" />
          <h2 className="text-base font-semibold">Prediction</h2>
        </div>
        <span className={`rounded-md px-2 py-1 text-xs font-semibold ${riskClasses[riskLabel]}`}>{riskLabel}</span>
      </div>
      <div className="space-y-3">
        <div>
          <p className="text-4xl font-semibold">{probability}%</p>
          <p className="text-sm text-slate-500">delay probability</p>
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
