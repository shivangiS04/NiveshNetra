import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { FundResult } from '../types'

interface Props { funds: FundResult[]; dark?: boolean }

export function InvestmentGrowthChart({ funds }: Props) {
  const inv = funds.reduce((s, f) => s + f.totalInvested, 0)
  const cur = funds.reduce((s, f) => s + f.currentValue, 0)
  const data = [
    { label: 'Invested', invested: Math.round(inv), current: Math.round(inv) },
    { label: 'Now',      invested: Math.round(inv), current: Math.round(cur) },
  ]
  const fmt = (v: number) => `₹${(v / 1000).toFixed(0)}K`

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <p className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-4">Investment Growth</p>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
          <XAxis dataKey="label" tick={{ fontSize: 12, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
          <YAxis tickFormatter={fmt} tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} width={40} />
          <Tooltip formatter={(v: number) => `₹${Math.round(v).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
            contentStyle={{ fontSize: 12, borderRadius: 6, border: '1px solid #e5e7eb' }} />
          <Line type="monotone" dataKey="invested" name="Invested" stroke="#d1d5db"
            strokeWidth={2} strokeDasharray="4 4" dot={{ r: 4, fill: '#d1d5db' }} />
          <Line type="monotone" dataKey="current" name="Current Value" stroke="#6366f1"
            strokeWidth={2.5} dot={{ r: 5, fill: '#6366f1' }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
