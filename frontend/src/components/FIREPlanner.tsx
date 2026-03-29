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

const INFLATION_RATE = 0.06
const WITHDRAWAL_RATE = 0.04

function projectCorpusMonthly(corpus: number, sip: number, rate: number, months: number): number {
  const r = rate / 12
  let c = corpus
  for (let i = 0; i < months; i++) c = c * (1 + r) + sip
  return c
}

function buildChartData(
  age: number,
  corpus: number,
  sip: number,
  rate: number,
  targetCorpus: number,
  retireAge: number,
): FireChartPoint[] {
  const years = Math.max(0, retireAge - age)
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

function computeFireDate(corpus: number, sip: number, rate: number, target: number): string {
  const r = rate / 12
  let c = corpus
  const today = new Date()
  for (let m = 1; m <= 600; m++) {
    c = c * (1 + r) + sip
    if (c >= target) {
      const d = new Date(today.getFullYear(), today.getMonth() + m, 1)
      return d.toLocaleString('en-IN', { month: 'long', year: 'numeric' })
    }
  }
  return 'Beyond age 110'
}

function computeSipGap(corpus: number, rate: number, target: number, months: number): number {
  if (months <= 0) return 0
  const r = rate / 12
  const fvExisting = corpus * Math.pow(1 + r, months)
  const factor = r > 0 ? (Math.pow(1 + r, months) - 1) / r : months
  const needed = (target - fvExisting) / factor
  return Math.max(0, needed)
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
  const [retireAge, setRetireAge] = useState(60)
  const [result, setResult] = useState<FirePlanResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [whatIfSip, setWhatIfSip] = useState(0)
  const [whatIfRetireAge, setWhatIfRetireAge] = useState(0)

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
    setWhatIfRetireAge(0)
    try {
      const res = await fetch('/api/fire-plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          age, monthlyIncome: income, monthlyExpenses: expenses,
          existingCorpus: corpus, monthlySip: sip, riskAppetite: risk,
          retirementAge: retireAge,
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

  // Live what-if: recompute everything client-side when sliders change
  const effectiveRetireAge = whatIfRetireAge > 0 ? whatIfRetireAge : (result?.yearsToRetirement ? age + result.yearsToRetirement : retireAge)
  const effectiveSip = sip + whatIfSip
  const rate = RETURN_RATES[risk]

  const whatIfData = useMemo(() => {
    if (!result) return null
    const yearsToRetire = Math.max(0, effectiveRetireAge - age)
    const monthsToRetire = yearsToRetire * 12
    const annualExpenses = expenses * 12
    const inflatedExpenses = annualExpenses * Math.pow(1 + INFLATION_RATE, yearsToRetire)
    const target = inflatedExpenses / WITHDRAWAL_RATE
    const projected = projectCorpusMonthly(corpus, effectiveSip, rate, monthsToRetire)
    const onTrack = projected >= target
    const sipGap = computeSipGap(corpus, rate, target, monthsToRetire)
    const additionalNeeded = Math.max(0, sipGap - effectiveSip)
    const fireDate = computeFireDate(corpus, effectiveSip, rate, target)
    const chartData = buildChartData(age, corpus, effectiveSip, rate, target, effectiveRetireAge)
    const progressPct = Math.min(100, Math.round((projected / target) * 100))
    return { target, projected, onTrack, additionalNeeded, fireDate, chartData, progressPct, yearsToRetire }
  }, [result, effectiveRetireAge, effectiveSip, age, corpus, expenses, rate])

  const displayData = whatIfData ?? {
    target: result?.targetCorpus ?? 0,
    projected: result?.projectedCorpusAtRetirement ?? 0,
    onTrack: result?.onTrack ?? false,
    additionalNeeded: result?.additionalSipNeeded ?? 0,
    fireDate: result?.fireDate ?? '',
    chartData: result?.chartData ?? [],
    progressPct: result ? Math.min(100, Math.round((result.projectedCorpusAtRetirement / result.targetCorpus) * 100)) : 0,
    yearsToRetire: result?.yearsToRetirement ?? 0,
  }

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
              Current Age
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
            <label style={{ fontSize: 12, color: muted }}>
              Target Retirement Age
              <input type="number" min={age + 1} max={80} value={retireAge} onChange={e => setRetireAge(+e.target.value)} style={inputStyle} />
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
            background: displayData.onTrack ? (dark ? '#052e16' : '#f0fdf4') : (dark ? '#1c1917' : '#fefce8'),
            border: `1px solid ${displayData.onTrack ? '#16a34a' : '#ca8a04'}`,
            borderRadius: 12, padding: '20px 24px', marginBottom: 16, textAlign: 'center',
          }}>
            <p style={{ fontSize: 26, fontWeight: 700, color: displayData.onTrack ? '#16a34a' : '#ca8a04', margin: '0 0 4px' }}>
              {displayData.fireDate}
            </p>
            <p style={{ fontSize: 13, color: muted, margin: 0 }}>
              {displayData.onTrack
                ? `On track to retire at ${effectiveRetireAge}`
                : `Retire at ${effectiveRetireAge} — additional SIP needed`}
              {(whatIfSip > 0 || whatIfRetireAge > 0) && (
                <span style={{ color: '#4f46e5', fontWeight: 600 }}> · What-if scenario active</span>
              )}
            </p>
          </div>

          {/* Progress + SIP gap */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            <div style={{ background: card, borderRadius: 12, border: `1px solid ${border}`, padding: 20 }}>
              <p style={{ fontSize: 12, color: muted, margin: '0 0 8px' }}>Target vs Projected Corpus</p>
              <p style={{ fontSize: 13, color: text, margin: '0 0 6px' }}>
                {fmt(displayData.projected)} of {fmt(displayData.target)}
              </p>
              <div style={{ background: subtle, borderRadius: 4, height: 10, overflow: 'hidden' }}>
                <div style={{ width: `${displayData.progressPct}%`, height: '100%', background: displayData.progressPct >= 100 ? '#16a34a' : '#4f46e5', borderRadius: 4, transition: 'width 0.4s' }} />
              </div>
              <p style={{ fontSize: 11, color: muted, margin: '4px 0 0' }}>{displayData.progressPct}% of target</p>
            </div>

            <div style={{ background: card, borderRadius: 12, border: `1px solid ${border}`, padding: 20 }}>
              <p style={{ fontSize: 12, color: muted, margin: '0 0 8px' }}>SIP Gap to Retire at {effectiveRetireAge}</p>
              {displayData.additionalNeeded > 0 ? (
                <>
                  <p style={{ fontSize: 22, fontWeight: 700, color: '#f87171', margin: '0 0 4px' }}>
                    +{fmt(displayData.additionalNeeded)}/mo
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
              <LineChart data={displayData.chartData} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
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

          {/* What-if sliders */}
          <div style={{ background: card, borderRadius: 12, border: `1px solid ${border}`, padding: 20, marginBottom: 16 }}>
            <p style={{ fontSize: 12, fontWeight: 600, color: muted, textTransform: 'uppercase', letterSpacing: '0.08em', margin: '0 0 16px' }}>
              What-if Scenarios — updates live
            </p>

            {(() => {
              const sipSliderMax = Math.max(100000, Math.ceil((result.additionalSipNeeded * 1.5) / 10000) * 10000)
              const sipSliderStep = sipSliderMax > 100000 ? 1000 : 500
              return (
                <div style={{ marginBottom: 16 }}>
                  <p style={{ fontSize: 12, color: muted, margin: '0 0 6px' }}>
                    Increase SIP by <span style={{ color: text, fontWeight: 600 }}>₹{whatIfSip.toLocaleString('en-IN')}/month</span>
                  </p>
                  <input type="range" min={0} max={sipSliderMax} step={sipSliderStep} value={whatIfSip}
                    onChange={e => setWhatIfSip(+e.target.value)}
                    style={{ width: '100%', accentColor: '#4f46e5' }} />
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: muted, marginTop: 2 }}>
                    <span>₹0</span><span>₹{(sipSliderMax / 1000).toFixed(0)}K</span>
                  </div>
                </div>
              )
            })()}

            <div>
              <p style={{ fontSize: 12, color: muted, margin: '0 0 6px' }}>
                Change retirement age to <span style={{ color: text, fontWeight: 600 }}>{whatIfRetireAge > 0 ? whatIfRetireAge : retireAge}</span>
              </p>
              <input type="range" min={age + 1} max={75} step={1}
                value={whatIfRetireAge > 0 ? whatIfRetireAge : retireAge}
                onChange={e => setWhatIfRetireAge(+e.target.value)}
                style={{ width: '100%', accentColor: '#cc0000' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: muted, marginTop: 2 }}>
                <span>Age {age + 1}</span><span>Age 75</span>
              </div>
            </div>

            {(whatIfSip > 0 || whatIfRetireAge > 0) && (
              <div style={{ marginTop: 12, padding: '10px 14px', background: dark ? '#1e1b4b' : '#eef2ff', borderRadius: 8 }}>
                <p style={{ fontSize: 13, color: '#4f46e5', fontWeight: 600, margin: 0 }}>
                  New FIRE date: {displayData.fireDate} · Corpus: {fmt(displayData.projected)} / {fmt(displayData.target)}
                </p>
              </div>
            )}

            {(whatIfSip > 0 || whatIfRetireAge > 0) && (
              <button onClick={() => { setWhatIfSip(0); setWhatIfRetireAge(0) }}
                style={{ marginTop: 10, fontSize: 11, color: muted, background: 'none', border: `1px solid ${border}`, borderRadius: 4, padding: '4px 10px', cursor: 'pointer' }}>
                Reset what-if
              </button>
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
