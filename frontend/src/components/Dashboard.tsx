import { useState } from 'react'
import type { AnalysisResponse } from '../types'
import { MetricCard } from './MetricCard'
import { AllocationPieChart } from './AllocationPieChart'
import { XIRRBarChart } from './XIRRBarChart'
import { BenchmarkComparison } from './BenchmarkComparison'
import { OverlapMatrix } from './OverlapMatrix'
import { ExpenseRadar } from './ExpenseRadar'
import { RebalancingPlan } from './RebalancingPlan'
import { MoneyHealthScore } from './MoneyHealthScore'
import { InvestmentGrowthChart } from './InvestmentGrowthChart'
import { FIREPlanner } from './FIREPlanner'
import { TaxWizard } from './TaxWizard'

interface Props {
  data: AnalysisResponse
  onReset: () => void
  dark: boolean
  onToggleDark: () => void
}
function fmt(n: number) {
  const r = Math.round(n)
  if (r >= 1e7) return `₹${(r / 1e7).toFixed(2)}Cr`
  if (r >= 1e5) return `₹${(r / 1e5).toFixed(2)}L`
  return `₹${r.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
}

type Tab = 'portfolio' | 'fire' | 'tax'

export function Dashboard({ data, onReset, dark, onToggleDark }: Props) {
  const { funds, totalInvested, totalCurrentValue, portfolioXirr, absoluteReturn,
    overlaps, totalExpenseDragAnnual, rebalancingPlan, rebalancingActions, warnings } = data

  const [activeTab, setActiveTab] = useState<Tab>('portfolio')
  const [reportLoading, setReportLoading] = useState(false)

  const avoidableFees = Math.round(totalExpenseDragAnnual * 0.4)
  const xirrPct = portfolioXirr !== null ? `${(portfolioXirr * 100).toFixed(2)}%` : 'N/A'
  const absPct = `${(absoluteReturn * 100).toFixed(1)}%`

  // Pre-fill FIRE planner from portfolio
  const existingInvestments = funds.map(f => f.fundName)
  const prefillCorpus = Math.round(totalCurrentValue)

  const bg = dark ? '#0f1117' : '#f5f5f5'
  const card = dark ? '#1e2130' : 'white'
  const border = dark ? '#2e3347' : '#e5e7eb'
  const text = dark ? '#f3f4f6' : '#111827'
  const muted = dark ? '#9ca3af' : '#6b7280'
  const subtle = dark ? '#374151' : '#f9fafb'

  async function handleDownloadReport() {
    setReportLoading(true)
    try {
      const res = await fetch('/api/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('Report generation failed')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `NiveshNetra_Report_${new Date().toISOString().slice(0, 10)}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      alert('Could not generate report. Please try again.')
    } finally {
      setReportLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: bg, transition: 'background 0.2s' }}>
      {/* Top nav */}
      <div style={{ background: '#cc0000', color: 'white', padding: '8px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontWeight: 700, fontSize: 18 }}>ET</span>
          <span style={{ color: '#fca5a5' }}>|</span>
          <span style={{ color: '#fee2e2' }}>Economic Times</span>
          <span style={{ color: '#fca5a5' }}>|</span>
          <span style={{ color: '#fee2e2' }}>Wealth</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button onClick={handleDownloadReport} disabled={reportLoading}
            style={{ background: 'rgba(255,255,255,0.15)', border: '1px solid rgba(255,255,255,0.3)', borderRadius: 4, padding: '4px 12px', cursor: reportLoading ? 'not-allowed' : 'pointer', fontSize: 12, color: 'white', opacity: reportLoading ? 0.7 : 1 }}>
            {reportLoading ? '⏳ Generating…' : '⬇ Download Report'}
          </button>
          <button onClick={onToggleDark} title={dark ? 'Switch to light mode' : 'Switch to dark mode'}
            style={{ background: 'rgba(255,255,255,0.15)', border: 'none', borderRadius: 20, width: 32, height: 32, cursor: 'pointer', fontSize: 16, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            {dark ? '☀️' : '🌙'}
          </button>
          <button onClick={onReset}
            style={{ color: '#fee2e2', background: 'none', border: '1px solid #fca5a5', borderRadius: 4, padding: '2px 12px', cursor: 'pointer', fontSize: 12 }}>
            ← Upload New
          </button>
        </div>
      </div>

      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '32px 16px 64px' }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: text, margin: '0 0 4px' }}>NiveshNetra</h1>
        <p style={{ fontSize: 13, color: muted, margin: '0 0 16px' }}>Portfolio X-Ray · ET Money Mentor</p>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: `1px solid ${border}` }}>
          {([['portfolio', '📊 Portfolio'], ['fire', '🔥 FIRE Planner'], ['tax', '🧾 Tax Wizard']] as const).map(([tab, label]) => (
            <button key={tab} onClick={() => setActiveTab(tab)}
              style={{
                padding: '8px 18px', fontSize: 13, fontWeight: activeTab === tab ? 600 : 400,
                border: 'none', borderBottom: activeTab === tab ? '2px solid #cc0000' : '2px solid transparent',
                background: 'none', color: activeTab === tab ? '#cc0000' : muted, cursor: 'pointer',
                marginBottom: -1,
              }}>
              {label}
            </button>
          ))}
        </div>

        {activeTab === 'fire' && (
          <FIREPlanner dark={dark} prefillCorpus={prefillCorpus} />
        )}

        {activeTab === 'tax' && (
          <TaxWizard dark={dark} existingInvestments={existingInvestments} />
        )}

        {activeTab === 'portfolio' && (
          <>
            {warnings.length > 0 && (
              <div style={{ background: dark ? '#2d2000' : '#fffbeb', border: `1px solid ${dark ? '#854d0e' : '#fcd34d'}`, borderRadius: 12, padding: '12px 16px', marginBottom: 24 }}>
                {warnings.map((w, i) => <p key={i} style={{ fontSize: 12, color: dark ? '#fbbf24' : '#92400e', margin: 0 }}>⚠ {w}</p>)}
              </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 12, marginBottom: 24 }}>
              <MetricCard label="Total Invested" value={fmt(totalInvested)} sub={`${funds.length} funds`} dark={dark} />
              <MetricCard label="Current Value" value={fmt(totalCurrentValue)} highlight dark={dark} />
              <MetricCard label="XIRR" value={xirrPct} sub="annualised" dark={dark} />
              <MetricCard label="Absolute Return" value={absPct} sub="total gain" dark={dark} />
              <MetricCard label="Avoidable Fees/yr" value={`₹${avoidableFees.toLocaleString('en-IN')}`} sub="switch to Direct" warn dark={dark} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
              <AllocationPieChart funds={funds} dark={dark} />
              <XIRRBarChart funds={funds} dark={dark} />
            </div>

            <div style={{ marginBottom: 16 }}><BenchmarkComparison funds={funds} dark={dark} /></div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
              <OverlapMatrix overlaps={overlaps} dark={dark} />
              <ExpenseRadar funds={funds} totalExpenseDragAnnual={totalExpenseDragAnnual} dark={dark} />
            </div>

            <div style={{ marginBottom: 16 }}><MoneyHealthScore data={data} dark={dark} /></div>
            <div style={{ marginBottom: 16 }}><RebalancingPlan plan={rebalancingPlan} actions={rebalancingActions} dark={dark} /></div>
            <div style={{ marginBottom: 16 }}><InvestmentGrowthChart funds={funds} dark={dark} /></div>

            {/* Fund table */}
            <div style={{ background: card, borderRadius: 12, border: `1px solid ${border}`, overflow: 'hidden', marginBottom: 16 }}>
              <div style={{ padding: '16px 20px', borderBottom: `1px solid ${border}` }}>
                <p style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.1em', color: muted, margin: 0 }}>Fund Details</p>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                  <thead>
                    <tr style={{ background: subtle }}>
                      {['Fund', 'Invested', 'Current', 'XIRR', 'Abs Return', 'Exp Ratio'].map((h, i) => (
                        <th key={i} style={{ padding: '10px 16px', textAlign: i === 0 ? 'left' : 'right', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: muted }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {funds.map((f, i) => (
                      <tr key={i} style={{ borderTop: `1px solid ${border}`, background: i % 2 !== 0 ? subtle : card }}>
                        <td style={{ padding: '10px 16px' }}>
                          <p style={{ fontWeight: 500, color: text, margin: 0, maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={f.fundName}>{f.fundName}</p>
                          {f.category && <p style={{ fontSize: 10, color: muted, margin: 0 }}>{f.category}</p>}
                        </td>
                        <td style={{ padding: '10px 16px', textAlign: 'right', color: muted }}>{fmt(Math.round(f.totalInvested))}</td>
                        <td style={{ padding: '10px 16px', textAlign: 'right', fontWeight: 600, color: text }}>{fmt(Math.round(f.currentValue))}</td>
                        <td style={{ padding: '10px 16px', textAlign: 'right', fontWeight: 600, color: f.xirr === null ? muted : f.xirr >= 0 ? '#818cf8' : '#f87171' }}>
                          {f.xirr !== null ? `${(f.xirr * 100).toFixed(2)}%` : '—'}
                        </td>
                        <td style={{ padding: '10px 16px', textAlign: 'right', color: f.absoluteReturn >= 0 ? '#4ade80' : '#f87171' }}>
                          {(f.absoluteReturn * 100).toFixed(1)}%
                        </td>
                        <td style={{ padding: '10px 16px', textAlign: 'right', color: muted }}>
                          {f.expenseRatio !== null ? `${(f.expenseRatio * 100).toFixed(2)}%` : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Footer */}
            <p style={{ textAlign: 'center', fontSize: 11, color: muted, marginTop: 8 }}>
              NiveshNetra · Built for ET Hackathon · AI by Groq Llama 3.3 70B
            </p>
            <p style={{ textAlign: 'center', fontSize: 12, color: muted, marginTop: 4 }}>
              Made with ❤️ by <span style={{ fontWeight: 600, color: '#cc0000' }}>Shivangi Singh</span>
            </p>
          </>
        )}
      </div>
    </div>
  )
}
