import type { AnalysisResponse } from '../types'
import { AllocationPieChart } from './AllocationPieChart'
import { InvestmentGrowthChart } from './InvestmentGrowthChart'
import { MetricCard } from './MetricCard'
import { XIRRBarChart } from './XIRRBarChart'

interface Props {
  data: AnalysisResponse
  onReset: () => void
}

function formatINR(v: number): string {
  return `₹${v.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
}

function formatXIRR(v: number | null): string {
  if (v === null) return 'N/A'
  return `${(v * 100).toFixed(2)}%`
}

function formatReturn(v: number): string {
  const sign = v >= 0 ? '+' : ''
  return `${sign}${(v * 100).toFixed(2)}%`
}

export function Dashboard({ data, onReset }: Props) {
  const gain = data.totalCurrentValue - data.totalInvested

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-50 p-6">
      <div className="max-w-6xl mx-auto">

        {/* Top bar */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-indigo-700">NiveshNetra</h1>
            <p className="text-gray-500 text-sm mt-1">Portfolio Analysis</p>
          </div>
          <button
            onClick={onReset}
            className="px-4 py-2 text-sm font-medium text-indigo-600 border border-indigo-300 rounded-xl hover:bg-indigo-50 transition-colors"
          >
            ↑ Upload New Statement
          </button>
        </div>

        {/* Warnings */}
        {data.warnings.length > 0 && (
          <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-xl text-amber-700 text-sm">
            <strong>Note:</strong> {data.warnings.join(' · ')}
          </div>
        )}

        {/* Metric cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <MetricCard
            label="Total Invested"
            value={formatINR(data.totalInvested)}
          />
          <MetricCard
            label="Current Value"
            value={formatINR(data.totalCurrentValue)}
            sub={`${gain >= 0 ? '+' : ''}${formatINR(gain)}`}
          />
          <MetricCard
            label="Portfolio XIRR"
            value={formatXIRR(data.portfolioXirr)}
            sub="Annualised return"
            highlight
          />
          <MetricCard
            label="Absolute Return"
            value={formatReturn(data.absoluteReturn)}
            sub="Total gain/loss"
          />
        </div>

        {/* Charts — top row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <AllocationPieChart funds={data.funds} />
          <XIRRBarChart funds={data.funds} />
        </div>

        {/* Charts — bottom row */}
        <div className="mb-6">
          <InvestmentGrowthChart funds={data.funds} />
        </div>

        {/* Fund table */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100">
            <h3 className="text-base font-semibold text-gray-700">Fund Details</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wide">
                <tr>
                  <th className="px-6 py-3 text-left">Fund</th>
                  <th className="px-6 py-3 text-right">Invested</th>
                  <th className="px-6 py-3 text-right">Current Value</th>
                  <th className="px-6 py-3 text-right">XIRR</th>
                  <th className="px-6 py-3 text-right">Abs. Return</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {data.funds.map((f, i) => (
                  <tr key={i} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 font-medium text-gray-800">{f.fundName}</td>
                    <td className="px-6 py-4 text-right text-gray-600">{formatINR(f.totalInvested)}</td>
                    <td className="px-6 py-4 text-right text-gray-600">{formatINR(f.currentValue)}</td>
                    <td className={`px-6 py-4 text-right font-semibold ${f.xirr === null ? 'text-gray-400' : f.xirr >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                      {formatXIRR(f.xirr)}
                    </td>
                    <td className={`px-6 py-4 text-right font-semibold ${f.absoluteReturn >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                      {formatReturn(f.absoluteReturn)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  )
}
