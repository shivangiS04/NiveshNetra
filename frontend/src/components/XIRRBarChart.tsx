import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { FundResult } from '../types'

interface Props {
  funds: FundResult[]
}

export function XIRRBarChart({ funds }: Props) {
  const data = funds.map(f => ({
    name: f.fundName.split(' ').slice(0, 3).join(' '),
    xirr: f.xirr !== null ? +(f.xirr * 100).toFixed(2) : null,
    label: f.xirr !== null ? `${(f.xirr * 100).toFixed(1)}%` : 'N/A',
  }))

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
      <h3 className="text-base font-semibold text-gray-700 mb-4">XIRR by Fund</h3>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} margin={{ top: 20, right: 20, left: 0, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 11, fill: '#6b7280' }}
            angle={-35}
            textAnchor="end"
            interval={0}
          />
          <YAxis
            unit="%"
            tick={{ fontSize: 11, fill: '#6b7280' }}
            domain={['auto', 'auto']}
          />
          <Tooltip
            formatter={(v) => v !== null ? `${v}%` : 'N/A'}
            labelStyle={{ color: '#374151' }}
          />
          <Bar dataKey="xirr" radius={[6, 6, 0, 0]}>
            {data.map((entry, i) => (
              <Cell
                key={i}
                fill={entry.xirr === null ? '#d1d5db' : entry.xirr >= 0 ? '#6366f1' : '#f87171'}
              />
            ))}
            <LabelList
              dataKey="label"
              position="top"
              style={{ fontSize: 11, fill: '#374151', fontWeight: 600 }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
