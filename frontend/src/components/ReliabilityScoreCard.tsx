import { ShieldCheck } from 'lucide-react'
import type { DelaySummary } from '../types/transit'

export function ReliabilityScoreCard({ summary }: { summary: DelaySummary | null }) {
  const score = summary?.reliability_score ?? 100
  const color = score >= 70 ? 'text-emerald-700' : score >= 40 ? 'text-amber-700' : 'text-red-700'

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center gap-2">
        <ShieldCheck className="h-5 w-5 text-emerald-700" />
        <h2 className="text-base font-semibold">Reliability</h2>
      </div>
      <p className={`text-5xl font-semibold ${color}`}>{score}</p>
      <p className="text-sm text-slate-500">score out of 100</p>
      <div className="mt-4 h-2 rounded-full bg-slate-100">
        <div className="h-2 rounded-full bg-emerald-700" style={{ width: `${Math.max(0, Math.min(100, score))}%` }} />
      </div>
      <p className="mt-3 text-sm text-slate-600">{summary?.sample_size ?? 0} observations in this route sample.</p>
    </div>
  )
}
