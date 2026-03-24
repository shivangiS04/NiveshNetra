import type { OverlapResult } from '../types'

interface Props { overlaps: OverlapResult[]; dark?: boolean }

function shortName(name: string) {
  const l = name.toLowerCase()
  if (l.includes('mirae')) return 'Mirae'
  if (l.includes('axis')) return 'Axis'
  if (l.includes('parag')) return 'PPFAS'
  if (l.includes('sbi small')) return 'SBI SC'
  return name.split(' ')[0]
}

function badge(pct: number) {
  if (pct >= 50) return 'bg-red-50 text-red-600 border border-red-200'
  if (pct >= 20) return 'bg-amber-50 text-amber-600 border border-amber-200'
  return 'bg-green-50 text-green-600 border border-green-200'
}

function bar(pct: number) {
  if (pct >= 50) return 'bg-red-400'
  if (pct >= 20) return 'bg-amber-400'
  return 'bg-green-400'
}

export function OverlapMatrix({ overlaps }: Props) {
  if (overlaps.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <p className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-3">Fund Overlap</p>
        <p className="text-sm text-green-600">No significant overlap detected.</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <p className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-1">Fund Overlap</p>
      <p className="text-xs text-gray-400 mb-4">High overlap = paying for the same stocks twice.</p>
      <div className="space-y-4">
        {overlaps.map((o, i) => {
          const pct = Math.round(o.overlapPct * 100)
          return (
            <div key={i}>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-sm font-medium text-gray-700">
                  {shortName(o.fundA)} ↔ {shortName(o.fundB)}
                </span>
                <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${badge(pct)}`}>
                  {pct}%
                </span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-1 mb-2">
                <div className={`h-1 rounded-full ${bar(pct)}`} style={{ width: `${pct}%` }} />
              </div>
              <div className="flex flex-wrap gap-1">
                {o.sharedStocks.slice(0, 5).map((s, j) => (
                  <span key={j} className="text-[11px] bg-gray-50 border border-gray-200 text-gray-500 px-2 py-0.5 rounded-full">
                    {s}
                  </span>
                ))}
                {o.sharedStocks.length > 5 && (
                  <span className="text-[11px] text-gray-400">+{o.sharedStocks.length - 5}</span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
