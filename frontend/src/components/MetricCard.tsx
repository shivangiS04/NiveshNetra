interface Props {
  label: string
  value: string
  sub?: string
  highlight?: boolean
}

export function MetricCard({ label, value, sub, highlight }: Props) {
  return (
    <div className={`rounded-2xl p-6 shadow-sm border ${highlight ? 'bg-indigo-600 text-white border-indigo-700' : 'bg-white text-gray-800 border-gray-100'}`}>
      <p className={`text-sm font-medium mb-1 ${highlight ? 'text-indigo-200' : 'text-gray-500'}`}>{label}</p>
      <p className={`text-2xl font-bold ${highlight ? 'text-white' : 'text-gray-900'}`}>{value}</p>
      {sub && <p className={`text-xs mt-1 ${highlight ? 'text-indigo-200' : 'text-gray-400'}`}>{sub}</p>}
    </div>
  )
}
