import { Bar, BarChart, CartesianGrid, Cell, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { FundResult } from '../types'

const SHORT: [string, string][] = [
  ['mirae', 'Mirae'], ['axis', 'Axis'], ['parag', 'PPFAS'], ['sbi small', 'SBI SC'],
]
function shortLabel(name: string) {
  const l = name.toLowerCase()
  for (const [k, v] of SHORT) if (l.includes(k)) return v
  return name.split(' ').slice(0, 2).join(' ')
}

interface Props { funds: FundResult[]; dark?: boolean }

export function BenchmarkComparison({ funds }: Props) {
  const data = funds
    .filter(f => f.xirr !== null && f.benchmarkXirr !== null)
    .map(f => ({
      name: shortLabel(f.fundName),
      'Fund': +((f.xirr! * 100).toFixed(1)),
      'Benchmark': +((f.benchmarkXirr! * 100).toFixed(1)),
      alpha: +((( f.xirr! - f.benchmarkXirr!) * 100).toFixed(1)),
    }))

  if (data.length === 0) return null

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <p className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-1">Fund vs Benchmark</p>
      <p className="text-xs text-gray-400 mb-4">Are your funds beating the index?</p>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
          <YAxis unit="%" tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false}
            domain={[0, 'auto']} width={32} />
          <Tooltip formatter={(v: number, name: string) => [`${v}%`, name]}
            contentStyle={{ fontSize: 12, borderRadius: 6, border: '1px solid #e5e7eb' }} />
          <Legend wrapperStyle={{ fontSize: 11, color: '#9ca3af' }} />
          <Bar dataKey="Fund" radius={[4, 4, 0, 0]} maxBarSize={36}>
            {data.map((e, i) => <Cell key={i} fill={e.alpha >= 0 ? '#6366f1' : '#f87171'} />)}
          </Bar>
          <Bar dataKey="Benchmark" fill="#e5e7eb" radius={[4, 4, 0, 0]} maxBarSize={36} />
        </BarChart>
      </ResponsiveContainer>
      <div className="mt-3 flex flex-wrap gap-1.5">
        {data.map((d, i) => (
          <span key={i} className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${
            d.alpha >= 0 ? 'bg-indigo-50 text-indigo-600' : 'bg-red-50 text-red-500'
          }`}>
            {d.name} {d.alpha >= 0 ? '+' : ''}{d.alpha}%
          </span>
        ))}
      </div>
    </div>
  )
}
