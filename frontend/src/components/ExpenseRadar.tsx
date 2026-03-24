import type { FundResult } from '../types'

interface Props {
  funds: FundResult[]
  totalExpenseDragAnnual: number
  dark?: boolean
}

function shortName(name: string) {
  const l = name.toLowerCase()
  if (l.includes('mirae')) return 'Mirae Large'
  if (l.includes('axis')) return 'Axis Blue'
  if (l.includes('parag')) return 'PPFAS Flexi'
  if (l.includes('sbi small')) return 'SBI Small'
  return name.split(' ').slice(0, 2).join(' ')
}

export function ExpenseRadar({ funds, totalExpenseDragAnnual }: Props) {
  const fundsWithData = funds.filter(f => f.expenseRatio !== null)
  const savings = Math.round(totalExpenseDragAnnual * 0.4)

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <p className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-1">Expense Drag</p>
      <p className="text-xs text-gray-400 mb-4">
        Paying <span className="font-semibold text-red-500">₹{Math.round(totalExpenseDragAnnual).toLocaleString('en-IN')}/yr</span> in fees.
      </p>

      <div className="space-y-3 mb-4">
        {fundsWithData.map((f, i) => {
          const er = (f.expenseRatio ?? 0) * 100
          const drag = Math.round(f.expenseDragAnnual)
          const w = Math.min((er / 2.5) * 100, 100)
          const c = er > 1.8 ? 'bg-red-400' : er > 1.2 ? 'bg-amber-400' : 'bg-green-400'
          return (
            <div key={i}>
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs text-gray-600">{shortName(f.fundName)}</span>
                <span className="text-xs font-semibold text-gray-700">
                  {er.toFixed(2)}% <span className="text-gray-400 font-normal">· ₹{drag.toLocaleString('en-IN')}/yr</span>
                </span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-1.5">
                <div className={`h-1.5 rounded-full ${c}`} style={{ width: `${w}%` }} />
              </div>
            </div>
          )
        })}
      </div>

      <div className="border-l-2 border-green-400 pl-3 py-1">
        <p className="text-xs font-semibold text-gray-700">
          Switch to Direct → save <span className="text-green-600">₹{savings.toLocaleString('en-IN')}/yr</span>
        </p>
        <p className="text-[11px] text-gray-400 mt-0.5">Model total · per-fund cards are estimates</p>
      </div>
    </div>
  )
}
