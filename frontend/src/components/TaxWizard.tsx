import { useState } from 'react'
import type { TaxPlanResponse } from '../types'

interface Props {
  dark: boolean
  existingInvestments?: string[]
}

function fmt(n: number) {
  if (n >= 1e5) return `₹${(n / 1e5).toFixed(2)}L`
  return `₹${Math.round(n).toLocaleString('en-IN')}`
}

export function TaxWizard({ dark, existingInvestments = [] }: Props) {
  const card = dark ? '#1e2130' : 'white'
  const border = dark ? '#2e3347' : '#e5e7eb'
  const text = dark ? '#f3f4f6' : '#111827'
  const muted = dark ? '#9ca3af' : '#6b7280'
  const subtle = dark ? '#374151' : '#f9fafb'
  const inputBg = dark ? '#111827' : 'white'

  const [basic, setBasic] = useState(600000)
  const [hra, setHra] = useState(200000)
  const [special, setSpecial] = useState(100000)
  const [other, setOther] = useState(0)
  const [rent, setRent] = useState(180000)
  const [city, setCity] = useState<'metro' | 'non-metro'>('metro')
  const [s80c, setS80c] = useState(100000)
  const [s80d, setS80d] = useState(15000)
  const [homeLoan, setHomeLoan] = useState(0)
  const [nps, setNps] = useState(0)
  const [otherDed, setOtherDed] = useState(0)

  const [result, setResult] = useState<TaxPlanResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const inputStyle = {
    width: '100%', padding: '8px 10px', borderRadius: 6,
    border: `1px solid ${border}`, background: inputBg,
    color: text, fontSize: 13, boxSizing: 'border-box' as const,
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const res = await fetch('/api/tax-plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          basicSalary: basic, hra, specialAllowance: special, otherAllowance: other,
          rentPaid: rent, cityType: city,
          section80C: s80c, section80D: s80d,
          homeLoanInterest: homeLoan, npsEmployer: nps, otherDeductions: otherDed,
          existingInvestments,
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

  function Section({ title, children }: { title: string; children: React.ReactNode }) {
    return (
      <div style={{ marginBottom: 20 }}>
        <p style={{ fontSize: 11, fontWeight: 600, color: muted, textTransform: 'uppercase', letterSpacing: '0.08em', margin: '0 0 10px' }}>{title}</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>{children}</div>
      </div>
    )
  }

  function Field({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
    return (
      <label style={{ fontSize: 12, color: muted }}>
        {label}
        <input type="number" min={0} value={value} onChange={e => onChange(+e.target.value)} style={inputStyle} />
      </label>
    )
  }

  return (
    <div style={{ padding: '24px 0' }}>
      {/* Form */}
      <div style={{ background: card, borderRadius: 12, border: `1px solid ${border}`, padding: 24, marginBottom: 20 }}>
        <p style={{ fontSize: 13, fontWeight: 600, color: muted, textTransform: 'uppercase', letterSpacing: '0.08em', margin: '0 0 16px' }}>
          Tax Wizard — FY 2024-25
        </p>
        <form onSubmit={handleSubmit}>
          <Section title="Salary Components">
            <Field label="Basic Salary (₹/yr)" value={basic} onChange={setBasic} />
            <Field label="HRA (₹/yr)" value={hra} onChange={setHra} />
            <Field label="Special Allowance (₹/yr)" value={special} onChange={setSpecial} />
            <Field label="Other Allowance (₹/yr)" value={other} onChange={setOther} />
            <Field label="Rent Paid (₹/yr)" value={rent} onChange={setRent} />
            <label style={{ fontSize: 12, color: muted }}>
              City Type
              <select value={city} onChange={e => setCity(e.target.value as 'metro' | 'non-metro')}
                style={{ ...inputStyle, marginTop: 0 }}>
                <option value="metro">Metro</option>
                <option value="non-metro">Non-Metro</option>
              </select>
            </label>
          </Section>

          <Section title="Deductions">
            <Field label="Section 80C (max ₹1.5L)" value={s80c} onChange={setS80c} />
            <Field label="Section 80D — Health Insurance (max ₹25K)" value={s80d} onChange={setS80d} />
            <Field label="Home Loan Interest 24b (max ₹2L)" value={homeLoan} onChange={setHomeLoan} />
            <Field label="NPS Employer 80CCD(2) (₹)" value={nps} onChange={setNps} />
            <Field label="Other Deductions (₹)" value={otherDed} onChange={setOtherDed} />
          </Section>

          {error && <p style={{ color: '#f87171', fontSize: 12, marginBottom: 8 }}>{error}</p>}

          <button type="submit" disabled={loading}
            style={{
              background: '#cc0000', color: 'white', border: 'none', borderRadius: 8,
              padding: '10px 28px', fontSize: 13, fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.7 : 1,
            }}>
            {loading ? 'Computing…' : 'Compare Tax Regimes'}
          </button>
        </form>
      </div>

      {/* Results */}
      {result && (
        <>
          {/* Winner banner */}
          <div style={{
            background: dark ? '#052e16' : '#f0fdf4',
            border: '1px solid #16a34a', borderRadius: 12,
            padding: '16px 24px', marginBottom: 16, textAlign: 'center',
          }}>
            <p style={{ fontSize: 22, fontWeight: 700, color: '#16a34a', margin: '0 0 4px' }}>
              {result.winner === 'tie'
                ? 'Both regimes are equal'
                : `Switch to ${result.winner === 'old' ? 'Old' : 'New'} Regime and save ${fmt(result.savings)} this year`}
            </p>
            <p style={{ fontSize: 12, color: muted, margin: 0 }}>Gross Income: {fmt(result.grossIncome)}</p>
          </div>

          {/* Side-by-side regime cards */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            {(['old', 'new'] as const).map(regime => {
              const r = regime === 'old' ? result.oldRegime : result.newRegime
              const isWinner = result.winner === regime
              return (
                <div key={regime} style={{
                  background: card, borderRadius: 12,
                  border: `2px solid ${isWinner ? '#16a34a' : border}`,
                  padding: 20,
                }}>
                  <p style={{ fontSize: 13, fontWeight: 700, color: isWinner ? '#16a34a' : text, margin: '0 0 12px' }}>
                    {regime === 'old' ? 'Old Regime' : 'New Regime'} {isWinner ? '✓ Better' : ''}
                  </p>
                  <div style={{ fontSize: 12, color: muted }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span>Standard Deduction</span><span style={{ color: text }}>₹{r.standardDeduction.toLocaleString('en-IN')}</span>
                    </div>
                    {regime === 'old' && result.oldRegime.hraExemption !== undefined && (
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <span>HRA Exemption</span><span style={{ color: text }}>{fmt(result.oldRegime.hraExemption)}</span>
                      </div>
                    )}
                    {regime === 'old' && result.oldRegime.totalDeductions !== undefined && (
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <span>Total Deductions</span><span style={{ color: text }}>{fmt(result.oldRegime.totalDeductions)}</span>
                      </div>
                    )}
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span>Taxable Income</span><span style={{ color: text }}>{fmt(r.taxableIncome)}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span>Tax + Cess (4%)</span><span style={{ color: text }}>{fmt(r.taxBeforeCess)} + {fmt(r.cess)}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: `1px solid ${border}`, paddingTop: 8, marginTop: 8 }}>
                      <span style={{ fontWeight: 600, color: text }}>Total Tax</span>
                      <span style={{ fontWeight: 700, fontSize: 16, color: isWinner ? '#16a34a' : '#f87171' }}>{fmt(r.totalTax)}</span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Missing deductions */}
          {result.missingDeductions.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              {result.missingDeductions.map((m, i) => (
                <div key={i} style={{
                  background: dark ? '#1c1917' : '#fefce8',
                  border: `1px solid ${dark ? '#854d0e' : '#fcd34d'}`,
                  borderRadius: 10, padding: '12px 16px', marginBottom: 8,
                }}>
                  <p style={{ fontSize: 13, color: dark ? '#fbbf24' : '#92400e', margin: 0 }}>
                    ⚠ {m.message}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Recommendations */}
          {result.recommendations.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <p style={{ fontSize: 11, fontWeight: 600, color: muted, textTransform: 'uppercase', letterSpacing: '0.08em', margin: '0 0 10px' }}>
                Tax-Saving Recommendations
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
                {result.recommendations.map((rec, i) => (
                  <div key={i} style={{
                    background: card, borderRadius: 10,
                    border: `1px solid ${rec.alreadyCovered ? '#16a34a' : border}`,
                    padding: 16,
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
                      <p style={{ fontSize: 13, fontWeight: 600, color: text, margin: 0 }}>{rec.name}</p>
                      {rec.alreadyCovered && <span style={{ fontSize: 10, background: '#16a34a', color: 'white', borderRadius: 4, padding: '2px 6px' }}>Covered</span>}
                    </div>
                    <p style={{ fontSize: 11, color: muted, margin: '0 0 4px' }}>Section {rec.section} · Lock-in: {rec.lockIn} · Risk: {rec.risk}</p>
                    <p style={{ fontSize: 12, color: '#4f46e5', fontWeight: 600, margin: 0 }}>
                      Save up to {fmt(rec.taxSaving)} in tax
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* AI Summary */}
          {result.aiSummary && (
            <div style={{ background: dark ? '#1e1b4b' : '#eef2ff', borderRadius: 12, border: `1px solid ${dark ? '#3730a3' : '#c7d2fe'}`, padding: 20 }}>
              <p style={{ fontSize: 11, fontWeight: 600, color: '#6366f1', textTransform: 'uppercase', letterSpacing: '0.08em', margin: '0 0 8px' }}>AI Tax Advisor</p>
              <p style={{ fontSize: 13, color: text, margin: 0, lineHeight: 1.6 }}>{result.aiSummary}</p>
            </div>
          )}
        </>
      )}
    </div>
  )
}
