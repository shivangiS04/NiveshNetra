import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import type { FundResult } from '../types'

const COLORS = ['#6366f1', '#8b5cf6', '#f59e0b', '#10b981']

const ALIASES: [string, string][] = [
  ['mirae', 'Mirae Large'],
  ['axis', 'Axis Blue'],
  ['parag', 'PPFAS Flexi'],
  ['sbi small', 'SBI Small'],
]

function alias(name: string) {
  const l = name.toLowerCase()
  for (const [k, v] of ALIASES) if (l.includes(k)) return v
  return name.split(' ').slice(0, 2).join(' ')
}

interface Props { funds: FundResult[]; dark?: boolean }

export function AllocationPieChart({ funds }: Props) {
  const total = funds.reduce((s, f) => s + f.currentValue, 0)
  const data = funds.map(f => ({
    name: alias(f.fundName),
    value: Math.round(f.currentValue),
    pct: total > 0 ? ((f.currentValue / total) * 100).toFixed(1) : '0',
  }))

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <p className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-4">Portfolio Allocation</p>
      <div className="flex items-center gap-6">
        <div className="shrink-0" style={{ width: 140, height: 140 }}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={data} cx="50%" cy="50%" innerRadius={40} outerRadius={64}
                paddingAngle={2} dataKey="value" strokeWidth={0}>
                {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip formatter={(v: number) => `₹${v.toLocaleString('en-IN')}`}
                contentStyle={{ fontSize: 12, borderRadius: 6, border: '1px solid #e5e7eb' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="flex-1 space-y-2.5">
          {data.map((d, i) => (
            <div key={i} className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full shrink-0" style={{ background: COLORS[i % COLORS.length] }} />
              <span className="text-xs text-gray-600 flex-1 truncate">{d.name}</span>
              <span className="text-xs font-semibold text-gray-800">{d.pct}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
