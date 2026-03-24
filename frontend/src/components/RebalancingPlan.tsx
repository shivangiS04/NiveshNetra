import type { RebalancingAction } from '../types'

interface Props {
  plan: string
  actions: RebalancingAction[]
  dark?: boolean
}

const CFG: Record<string, { label: string; border: string; tag: string; impact: string }> = {
  switch: { label: 'Switch',      border: 'border-l-green-500',  tag: 'text-green-600 bg-green-50',  impact: 'text-green-600' },
  reduce: { label: 'Reduce',      border: 'border-l-amber-400',  tag: 'text-amber-600 bg-amber-50',  impact: 'text-amber-600' },
  exit:   { label: 'Exit',        border: 'border-l-red-500',    tag: 'text-red-600 bg-red-50',      impact: 'text-red-600'   },
  enter:  { label: 'Enter',       border: 'border-l-blue-500',   tag: 'text-blue-600 bg-blue-50',    impact: 'text-blue-600'  },
  action: { label: 'Action Item', border: 'border-l-indigo-500', tag: 'text-indigo-600 bg-indigo-50',impact: 'text-indigo-600'},
}

export function RebalancingPlan({ plan, actions }: Props) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-center gap-2 mb-4">
        <p className="text-xs font-semibold uppercase tracking-widest text-gray-400">AI Rebalancing Plan</p>
        <span className="text-[11px] text-gray-300">· Groq Llama 3.3 70B</span>
      </div>

      {actions.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
          {actions.map((a, i) => {
            const c = CFG[a.type] ?? CFG.action
            return (
              <div key={i} className={`border-l-[3px] ${c.border} bg-gray-50 rounded-r-lg px-4 py-3`}>
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-[10px] font-bold uppercase tracking-widest px-1.5 py-0.5 rounded ${c.tag}`}>
                    {c.label}
                  </span>
                  <span className="text-xs font-semibold text-gray-700 truncate">{a.fund}</span>
                </div>
                <p className="text-xs text-gray-500 mb-1.5">{a.detail}</p>
                <p className={`text-xs font-bold ${c.impact}`}>{a.impact}</p>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
