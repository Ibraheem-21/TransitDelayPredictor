import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { DelayBucket } from '../types/transit'

type Props = {
  title: string
  subtitle?: string
  data: DelayBucket[]
  xKey: 'hour' | 'day'
}

export function DelayChart({ title, subtitle, data, xKey }: Props) {
  return (
    <div className="h-80 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-4">
        <h2 className="text-base font-semibold">{title}</h2>
        {subtitle && <p className="mt-1 text-xs text-slate-500">{subtitle}</p>}
      </div>
      <ResponsiveContainer width="100%" height="85%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Bar dataKey="average_delay" fill="#047857" radius={[4, 4, 0, 0]} name="Average delay" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
