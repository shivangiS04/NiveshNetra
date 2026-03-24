interface Props {
  label: string
  value: string
  sub?: string
  highlight?: boolean
  warn?: boolean
  dark?: boolean
}

export function MetricCard({ label, value, sub, highlight, warn, dark }: Props) {
  const bg = highlight ? '#4f46e5' : warn ? (dark ? '#1e2130' : 'white') : (dark ? '#1e2130' : 'white')
  const borderStyle = warn
    ? `1px solid ${dark ? '#374151' : '#e5e7eb'}`
    : highlight ? '1px solid #4f46e5' : `1px solid ${dark ? '#2e3347' : '#e5e7eb'}`
  const labelColor = highlight ? '#c7d2fe' : warn ? '#f87171' : (dark ? '#9ca3af' : '#9ca3af')
  const valueColor = highlight ? 'white' : warn ? '#f87171' : (dark ? '#f3f4f6' : '#111827')
  const subColor = highlight ? '#c7d2fe' : warn ? '#fca5a5' : (dark ? '#6b7280' : '#9ca3af')

  return (
    <div style={{
      background: bg,
      border: borderStyle,
      borderLeft: warn ? '3px solid #ef4444' : borderStyle,
      borderRadius: 12,
      padding: '16px 20px',
    }}>
      <p style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.1em', color: labelColor, margin: '0 0 6px' }}>{label}</p>
      <p style={{ fontSize: 24, fontWeight: 700, color: valueColor, margin: 0, lineHeight: 1 }}>{value}</p>
      {sub && <p style={{ fontSize: 11, color: subColor, margin: '6px 0 0' }}>{sub}</p>}
    </div>
  )
}
