import type { AnalysisResponse } from '../types'

interface Props { data: AnalysisResponse; dark?: boolean }

interface Dim { label: string; score: number; insight: string }

function computeDims(data: AnalysisResponse): Dim[] {
  const { funds, overlaps, totalExpenseDragAnnual, portfolioXirr, totalCurrentValue } = data
  const cats = new Set(funds.map(f => f.category).filter(Boolean))
  const hi = overlaps.filter(o => o.overlapPct >= 0.5).length
  const divScore = Math.max(20, Math.min(100, (cats.size / 4) * 60 + (hi === 0 ? 40 : hi === 1 ? 20 : 0)))
  const er = totalCurrentValue > 0 ? totalExpenseDragAnnual / totalCurrentValue : 0
  const expScore = Math.max(10, Math.min(100, Math.round(100 - ((er - 0.005) / (0.02 - 0.005)) * 80)))
  const xirr = portfolioXirr ?? 0
  const retScore = Math.max(10, Math.min(100, Math.round((xirr / 0.15) * 100)))
  const wb = funds.filter(f => f.xirr !== null && f.benchmarkXirr !== null)
  const beat = wb.filter(f => (f.xirr ?? 0) >= (f.benchmarkXirr ?? 0))
  const benchScore = wb.length > 0 ? Math.round((beat.length / wb.length) * 100) : 50
  const corpScore = Math.min(100, Math.round((totalCurrentValue / 500000) * 60 + 20))
  const conScore = Math.min(100, funds.length * 20 + 20)
  return [
    { label: 'Diversification',    score: Math.round(divScore),  insight: hi > 0 ? `${hi} pair(s) >50% overlap` : `${cats.size} categories` },
    { label: 'Expense Efficiency', score: expScore,               insight: `${(er*100).toFixed(2)}% avg ER · save ~₹${Math.round(totalExpenseDragAnnual*0.4).toLocaleString('en-IN')}/yr` },
    { label: 'Return Quality',     score: retScore,               insight: `XIRR ${(xirr*100).toFixed(1)}% vs 12% target` },
    { label: 'Benchmark Align',    score: benchScore,             insight: `${beat.length}/${wb.length} funds beating index` },
    { label: 'Corpus Growth',      score: corpScore,              insight: `₹${(totalCurrentValue/100000).toFixed(1)}L portfolio` },
    { label: 'Consistency',        score: conScore,               insight: `${funds.length} fund(s) tracked` },
  ]
}

function ringColor(s: number) { return s >= 75 ? '#22c55e' : s >= 50 ? '#f59e0b' : '#ef4444' }
function barCls(s: number)    { return s >= 75 ? 'bg-green-500' : s >= 50 ? 'bg-amber-400' : 'bg-red-400' }
function numCls(s: number)    { return s >= 75 ? 'text-green-600' : s >= 50 ? 'text-amber-500' : 'text-red-500' }
function gradeLabel(s: number){ return s >= 80 ? 'Excellent' : s >= 65 ? 'Good' : s >= 50 ? 'Fair' : 'Needs Work' }

export function MoneyHealthScore({ data }: Props) {
  const dims = computeDims(data)
  const overall = Math.round(dims.reduce((s, d) => s + d.score, 0) / dims.length)
  const rc = ringColor(overall)
  const r = 42, circ = 2 * Math.PI * r, dash = (overall / 100) * circ

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <p className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-4">Money Health Score</p>

      <div className="flex gap-8 items-start">
        {/* Ring */}
        <div className="shrink-0 flex flex-col items-center gap-1">
          <svg width={100} height={100} viewBox="0 0 100 100">
            <circle cx={50} cy={50} r={r} fill="none" stroke="#f3f4f6" strokeWidth={9} />
            <circle cx={50} cy={50} r={r} fill="none" stroke={rc} strokeWidth={9}
              strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
              transform="rotate(-90 50 50)" />
            <text x={50} y={46} textAnchor="middle" fontSize={24} fontWeight={700} fill={rc}>{overall}</text>
            <text x={50} y={60} textAnchor="middle" fontSize={10} fill="#9ca3af">/ 100</text>
          </svg>
          <span className={`text-xs font-bold ${numCls(overall)}`}>{gradeLabel(overall)}</span>
          <span className="text-[10px] text-gray-400">equal-weight avg</span>
        </div>

        {/* Bars */}
        <div className="flex-1 space-y-2">
          {dims.map(d => (
            <div key={d.label}>
              <div className="flex justify-between items-center mb-0.5">
                <span className="text-[11px] font-semibold text-gray-600">{d.label}</span>
                <span className={`text-[11px] font-bold ${numCls(d.score)}`}
                  title={d.label === 'Expense Efficiency' ? '100=Direct-plan fees, low=Regular-plan fees' : 'out of 100'}>
                  {d.score}
                </span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-1">
                <div className={`h-1 rounded-full ${barCls(d.score)}`} style={{ width: `${d.score}%` }} />
              </div>
              <p className="text-[10px] text-gray-400 mt-0.5">{d.insight}</p>
            </div>
          ))}
        </div>
      </div>

      <p className="text-[11px] text-gray-400 mt-4 pt-3 border-t border-gray-100">
        <a href="https://economictimes.indiatimes.com/mf/analysis" target="_blank" rel="noopener noreferrer"
          className="text-[#cc0000] hover:underline">
          Why Direct plans outperform Regular — Economic Times ↗
        </a>
      </p>
    </div>
  )
}
