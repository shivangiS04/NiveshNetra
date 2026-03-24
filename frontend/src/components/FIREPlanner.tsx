import { useState, useMemo } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import type { FirePlanResponse, FireChartPoint } from '../types'

interface Props {
  dark: boolean
  prefillCorpus?: number
  prefillSip?: number
}

const RETURN_RATES: Record<string, number> = {
  conservative: 0.10,
  moderate: 0.12,
  aggressive: 0.14,
}

function projectCorpus(corpus: number, sip: number, rate: number, years: number): number {
  const r = rate / 12
  let c = corpus
  for (let i = 0; i < years * 12; i++) c = c * (1 + r) + sip
  return c
}

function buildChartData(
  age: number, corpus: number, sip: number, rate: number,
  targetCorpus: number, years: number,
): FireChartPoint[] {
  const r = rate / 12
  let c = corpus
  const data: FireChartPoint[] = []
  for (let y = 1; y <= years; y++) {
    for (let m = 0; m < 12; m++) c = c * (1 + r) + sip
    data.push({
      year: age + y,
      projected: Math.round(c),
      required: Math.round(targetCorpus * (y / years)),
    })
  }
  return data
}

function fmt(n: number) {
  if (n >= 1e7) return `₹${(n / 1e7).toFixed(2)}Cr`
  if (n >= 1e5) return `₹${(n / 1e5).toFixed(2)}L`
  return `₹${Math.round(n).toLocaleString('en-IN')}`
}

export function FIREPlanner({ dark, prefillCorpus = 0, prefillSip = 0 }: Props) {
  const card = dark ? '#1e2130' : 'white'
  const border = dark ? '#2e3347' : '#e5e7eb'
  const text = dark ? '#f3f4f6' : '#111827'
  const muted = dark ? '#9ca3af' : '#6b7280'
  const subtle = dark ? '#374151' : '#f9fafb'
  const inputBg = dark ? '#111827' : 'white'

  const [age, setAge] = useState(30)
  const [income, setIncome] = useState(100000)
  const [expenses, setExpenses] = useState(60000)
  const [corpus, setCorpus] = useState(prefillCorpus)
  const [sip, setSip] = useState(prefillSip || 10000)
  const [risk, setRisk] = useState<'conservative' | 'moderate' | 'aggressive'>('moderate')
  const [result, setResult] = useState<FirePlanResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [whatIfSip, setWhatIfSip] = useState(0)

  const inputStyle = {
    width: '100%', padding: '8px 10px', borderRadius: 6,
    border: `1px solid ${border}`, background: inputBg,
    color: text, fontSize: 13, boxSizing: 'border-box' as const,
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')
    setWhatIfSip(0)
    try {
      const res = await fetch('/api/fire-plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          age, monthlyIncome: income, monthlyExpenses: expenses,
          existingCorpus: corpus, monthlySip: sip, riskAppetite: risk,
        }),
      })
      if (!res.ok) throw new Error((await res.json()).detail || 'Request failed')
      setResult(await res.json())
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // What-if: recompute chart data client-side with extra SIP
  const whatIfChartData = useMemo(() => {
    if (!result || whatIfSip === 0) return result?.chartData ?? []
    const rate = RETURN_RATES[risk]
    const years = result.yearsToRetirement
    return buildChartData(age, corpus, sip + whatIfSip, rate, result.targetCorpus, years)
  }, [result, whatIfSip, age, corpus, sip, risk])

  const whatIfFireDate = useMemo(() => {
    if (!result || whatIfSip === 0) return result?.fireDate ?? ''
    const rate = RETURN_RATES[risk]
    const r = rate / 12
    let c = corpus
    const target = result.targetCorpus
    const today = new Date()
    for (let m = 1; m <= 600; m++) {
      c = c * (1 + r) + (sip + whatIfSip)
      if (c >= target) {
        const d = new Date(today.getFullYear(), today.getMonth() + m, 1)
        return d.toLocaleString('en-IN', { month: 'long', year: 'numeric' })
      }
    }
    return 'Beyond age 110'
  }, [result, whatIfSip, corpus, sip, risk])

  const chartData = whatIfSip > 0 ? whatIfChartData : (result?.chartData ?? [])
  const progressPct = result
    ? Math.min(100, Math.round((result.projectedCorpusAtRetirement / result.targetCorpus) * 100))
    : 0

  const riskBtns: Array<'conservative' | 'moderate' | 'aggressive'> = ['conservative', 'moderate', 'aggressive']

  return (
    <div style={{ padding: '24px 0' }}>
      {/* Input form */}
      <div style={{ background: card, borderRadius: 12, border: `1px solid ${border}`, padding: 24, marginBottom: 20 }}>
        <p style={{ fontSize: 13, fontWeight: 600, color: muted, textTransform: 'uppercase', letterSpacing: '0.08em', margin: '0 0 16px' }}>
          FIRE Path Planner
        </p>
        <form onSubmit={handleSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 16 }}>
            <label style={{ fontSize: 12, color: muted }}>
              Age
              <input type="number" min={18} max={59} value={age} onChange={e => setAge(+e.target.value)} style={inputStyle} />
            </label>
            <label style={{ fontSize: 12, color: muted }}>
              Monthly Income (₹)
              <input type="number" min={0} value={income} onChange={e => setIncome(+e.target.value)} style={inputStyle} />
            </label>
            <label style={{ fontSize: 12, color: muted }}>
              Monthly Expenses (₹)
              <input type="number" min={0} value={expenses} onChange={e => setExpenses(+e.target.value)} style={inputStyle} />
            </label>
            <label style={{ fontSize: 12, color: muted }}>
              Existing Corpus (₹)
              <input type="number" min={0} value={corpus} onChange={e => setCorpus(+e.target.value)} style={inputStyle} />
            </label>
            <label style={{ fontSize: 12, color: muted }}>
              Monthly SIP (₹)
              <input type="number" min={0} value={sip} onChange={e => setSip(+e.target.value)} style={inputStyle} />
            </label>
          </div>

          <div style={{ marginBottom: 20 }}>
            <p style={{ fontSize: 12, color: muted, margin: '0 0 8px' }}>Risk Appetite</p>
            <div style={{ display: 'flex', gap: 8 }}>
              {riskBtns.map(r => (
                <button key={r} type="button" onClick={() => setRisk(r)}
                  style={{
                    padding: '6px 18px', borderRadius: 20, fontSize: 12, cursor: 'pointer',
                    border: `1px solid ${risk === r ? '#4f46e5' : border}`,
                    background: risk === r ? '#4f46e5' : subtle,
                    color: risk === r ? 'white' : text, fontWeight: risk === r ? 600 : 400,
                  }}>
                  {r.charAt(0).toUpperCase() + r.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {error && <p style={{ color: '#f87171', fontSize: 12, marginBottom: 8 }}>{error}</p>}

          <button type="submit" disabled={loading}
            style={{
              background: '#cc0000', color: 'white', border: 'none', borderRadius: 8,
              padding: '10px 28px', fontSize: 13, fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.7 : 1,
            }}>
            {loading ? 'Computing…' : 'Calculate FIRE Date'}
          </button>
        </form>
      </div>

      {/* Results */}
      {result && (
        <>
          {/* Hero */}
          <div style={{
            background: result.onTrack ? (dark ? '#052e16' : '#f0fdf4') : (dark ? '#1c1917' : '#fefce8'),
            border: `1px solid ${result.onTrack ? '#16a34a' : '#ca8a04'}`,
            borderRadius: 12, padding: '20px 24px', marginBottom: 16, textAlign: 'center',
          }}>
            <p style={{ fontSize: 28, fontWeight: 700, color: result.onTrack ? '#16a34a' : '#ca8a04', margin: '0 0 4px' }}>
              {whatIfSip > 0 ? `With +₹${whatIfSip.toLocaleString('en-IN')}/mo SIP: ${whatIfFireDate}` : `You can retire in ${result.fireDate}`}
            </p>
            <p style={{ fontSize: 13, color: muted, margin: 0 }}>
              {result.onTrack
                ? `On track · ${result.yearsEarly} year(s) early`
                : `${result.yearsToRetirement} years to retirement · additional SIP needed`}
            </p>
          </div>

          {/* Progress bar + SIP gap */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            <div style={{ background: card, borderRadius: 12, border: `1px solid ${border}`, padding: 20 }}>
              <p style={{ fontSize: 12, color: muted, margin: '0 0 8px' }}>Target vs Projected Corpus</p>
              <p style={{ fontSize: 13, color: text, margin: '0 0 6px' }}>
                {fmt(result.projectedCorpusAtRetirement)} of {fmt(result.targetCorpus)}
              </p>
              <div style={{ background: subtle, borderRadius: 4, height: 10, overflow: 'hidden' }}>
                <div style={{ width: `${progressPct}%`, height: '100%', background: progressPct >= 100 ? '#16a34a' : '#4f46e5', borderRadius: 4, transition: 'width 0.5s' }} />
              </div>
              <p style={{ fontSize: 11, color: muted, margin: '4px 0 0' }}>{progressPct}% of target</p>
            </div>

            <div style={{ background: card, borderRadius: 12, border: `1px solid ${border}`, padding: 20 }}>
              <p style={{ fontSize: 12, color: muted, margin: '0 0 8px' }}>SIP Gap to Retire at 60</p>
              {result.additionalSipNeeded > 0 ? (
                <>
                  <p style={{ fontSize: 22, fontWeight: 700, color: '#f87171', margin: '0 0 4px' }}>
                    +{fmt(result.additionalSipNeeded)}/mo
                  </p>
                  <p style={{ fontSize: 12, color: muted, margin: 0 }}>additional SIP needed to retire on time</p>
                </>
              ) : (
                <p style={{ fontSize: 18, fontWeight: 700, color: '#16a34a', margin: 0 }}>No gap — you're on track!</p>
              )}
            </div>
          </div>

          {/* Chart */}
          <div style={{ background: card, borderRadius: 12, border: `1px solid ${border}`, padding: 20, marginBottom: 16 }}>
            <p style={{ fontSize: 12, color: muted, margin: '0 0 12px' }}>Corpus Growth Projection</p>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={chartData} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={border} />
                <XAxis dataKey="year" tick={{ fontSize: 11, fill: muted }} />
                <YAxis tickFormatter={v => v >= 1e7 ? `${(v/1e7).toFixed(1)}Cr` : `${(v/1e5).toFixed(0)}L`} tick={{ fontSize: 10, fill: muted }} width={52} />
                <Tooltip formatter={(v: number) => fmt(v)} labelFormatter={l => `Age ${l}`} contentStyle={{ background: card, border: `1px solid ${border}`, fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Line type="monotone" dataKey="projected" name="Your Trajectory" stroke="#4f46e5" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="required" name="Required Path" stroke="#f87171" strokeWidth={2} dot={false} strokeDasharray="5 5" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* What-if slider */}
          <div style={{ background: card, borderRadius: 12, border: `1px solid ${border}`, padding: 20, marginBottom: 16 }}>
            <p style={{ fontSize: 12, color: muted, margin: '0 0 8px' }}>What if? — Increase SIP by ₹{whatIfSip.toLocaleString('en-IN')}/month</p>
            <input type="range" min={0} max={50000} step={500} value={whatIfSip}
              onChange={e => setWhatIfSip(+e.target.value)}
              style={{ width: '100%', accentColor: '#4f46e5' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: muted, marginTop: 4 }}>
              <span>₹0</span><span>₹50,000</span>
            </div>
            {whatIfSip > 0 && (
              <p style={{ fontSize: 13, color: '#4f46e5', fontWeight: 600, margin: '8px 0 0' }}>
                New FIRE date: {whatIfFireDate}
              </p>
            )}
          </div>

          {/* Asset allocation table */}
          <div style={{ background: card, borderRadius: 12, border: `1px solid ${border}`, padding: 20, marginBottom: 16 }}>
            <p style={{ fontSize: 12, color: muted, margin: '0 0 12px' }}>Asset Allocation by Decade</p>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: subtle }}>
                  {['Decade', 'Equity', 'Debt'].map((h, i) => (
                    <th key={i} style={{ padding: '8px 12px', textAlign: i === 0 ? 'left' : 'center', fontSize: 11, fontWeight: 600, color: muted, textTransform: 'uppercase' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result.assetAllocation.map((row, i) => (
                  <tr key={i} style={{ borderTop: `1px solid ${border}` }}>
                    <td style={{ padding: '8px 12px', color: text, fontWeight: 500 }}>{row.decade}</td>
                    <td style={{ padding: '8px 12px', textAlign: 'center', color: '#4f46e5', fontWeight: 600 }}>{row.equity}%</td>
                    <td style={{ padding: '8px 12px', textAlign: 'center', color: '#f87171', fontWeight: 600 }}>{row.debt}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* AI Summary */}
          {result.aiSummary && (
            <div style={{ background: dark ? '#1e1b4b' : '#eef2ff', borderRadius: 12, border: `1px solid ${dark ? '#3730a3' : '#c7d2fe'}`, padding: 20 }}>
              <p style={{ fontSize: 11, fontWeight: 600, color: '#6366f1', textTransform: 'uppercase', letterSpacing: '0.08em', margin: '0 0 8px' }}>AI Advisor Summary</p>
              <p style={{ fontSize: 13, color: text, margin: 0, lineHeight: 1.6 }}>{result.aiSummary}</p>
            </div>
          )}
        </>
      )}
    </div>
  )
}
