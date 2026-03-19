import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { FundResult } from '../types'

interface Props {
  funds: FundResult[]
}

/**
 * Builds a simple two-point growth chart:
 * Point 1 = total invested (start)
 * Point 2 = current value (now)
 *
 * For a richer chart with real transaction history, the backend would need
 * to return time-series data. This gives a clean visual for the hackathon.
 */
export function InvestmentGrowthChart({ funds }: Props) {
  const totalInvested = funds.reduce((s, f) => s + f.totalInvested, 0)
  const totalCurrent = funds.reduce((s, f) => s + f.currentValue, 0)

  const data = [
    { label: 'Invested', invested: Math.round(totalInvested), current: Math.round(totalInvested) },
    { label: 'Now', invested: Math.round(totalInvested), current: Math.round(totalCurrent) },
  ]

  const formatINR = (v: number) => `₹${(v / 1000).toFixed(0)}K`

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
      <h3 className="text-base font-semibold text-gray-700 mb-4">Investment Growth</h3>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data} margin={{ top: 10, right: 20, left: 10, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="label" tick={{ fontSize: 12, fill: '#6b7280' }} />
          <YAxis tickFormatter={formatINR} tick={{ fontSize: 11, fill: '#6b7280' }} />
          <Tooltip formatter={(v: number) => `₹${v.toLocaleString('en-IN')}`} />
          <Legend />
          <Line
            type="monotone"
            dataKey="invested"
            name="Total Invested"
            stroke="#a78bfa"
            strokeWidth={2}
            dot={{ r: 5 }}
            strokeDasharray="5 5"
          />
          <Line
            type="monotone"
            dataKey="current"
            name="Current Value"
            stroke="#6366f1"
            strokeWidth={3}
            dot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
