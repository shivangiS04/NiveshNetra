import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { FundResult } from '../types'

const SHORT: [string, string][] = [
  ['mirae', 'Mirae'], ['axis', 'Axis'], ['parag', 'PPFAS'], ['sbi small', 'SBI SC'],
]
function shortLabel(name: string) {
  const l = name.toLowerCase()
  for (const [k, v] of SHORT) if (l.includes(k)) return v
  return name.split(' ')[0]
}

interface Props { funds: FundResult[]; dark?: boolean }

export function XIRRBarChart({ funds }: Props) {
  const data = funds.map(f => ({
    name: shortLabel(f.fundName),
    xirr: f.xirr !== null ? +(f.xirr * 100).toFixed(2) : null,
    label: f.xirr !== null ? `${(f.xirr * 100).toFixed(1)}%` : 'N/A',
  }))

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <p className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-4">XIRR by Fund</p>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} margin={{ top: 20, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
          <YAxis unit="%" tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false}
            domain={['auto', 'auto']} width={32} />
          <Tooltip formatter={(v) => v !== null ? `${v}%` : 'N/A'}
            contentStyle={{ fontSize: 12, borderRadius: 6, border: '1px solid #e5e7eb' }} />
          <Bar dataKey="xirr" radius={[4, 4, 0, 0]} maxBarSize={44}>
            {data.map((e, i) => (
              <Cell key={i} fill={e.xirr === null ? '#e5e7eb' : e.xirr >= 0 ? '#6366f1' : '#f87171'} />
            ))}
            <LabelList dataKey="label" position="top" style={{ fontSize: 11, fill: '#6b7280', fontWeight: 600 }} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
