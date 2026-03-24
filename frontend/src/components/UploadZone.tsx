import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import type { AnalysisResponse, ApiError } from '../types'

interface Props {
  onAnalysed: (data: AnalysisResponse) => void
  dark: boolean
  onToggleDark: () => void
}

function ManualPlanModal({ onClose }: { onClose: () => void }) {
  const [form, setForm] = useState({ age: '', monthlyIncome: '', monthlySip: '', riskAppetite: 'moderate', goal: 'retirement' })
  const [loading, setLoading] = useState(false)
  const [plan, setPlan] = useState<string | null>(null)

  const submit = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/quick-plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          age: Number(form.age),
          monthlyIncome: Number(form.monthlyIncome),
          monthlySip: Number(form.monthlySip),
          riskAppetite: form.riskAppetite,
          goal: form.goal,
        }),
      })
      const data = await res.json()
      setPlan(data.plan)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-indigo-700">Quick Financial Plan</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>

        {!plan ? (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Age</label>
                <input type="number" placeholder="30" value={form.age}
                  onChange={e => setForm(f => ({ ...f, age: e.target.value }))}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-400" />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Monthly Income (₹)</label>
                <input type="number" placeholder="80000" value={form.monthlyIncome}
                  onChange={e => setForm(f => ({ ...f, monthlyIncome: e.target.value }))}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-400" />
              </div>
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Monthly SIP Amount (₹)</label>
              <input type="number" placeholder="10000" value={form.monthlySip}
                onChange={e => setForm(f => ({ ...f, monthlySip: e.target.value }))}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-400" />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Risk Appetite</label>
              <select value={form.riskAppetite} onChange={e => setForm(f => ({ ...f, riskAppetite: e.target.value }))}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-400">
                <option value="conservative">Conservative</option>
                <option value="moderate">Moderate</option>
                <option value="aggressive">Aggressive</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Primary Goal</label>
              <select value={form.goal} onChange={e => setForm(f => ({ ...f, goal: e.target.value }))}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-400">
                <option value="retirement">Retirement</option>
                <option value="child's education">Child's Education</option>
                <option value="home purchase">Home Purchase</option>
                <option value="wealth creation">Wealth Creation</option>
              </select>
            </div>
            <button onClick={submit} disabled={loading || !form.age || !form.monthlyIncome || !form.monthlySip}
              className="w-full bg-indigo-600 text-white rounded-xl py-2.5 text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50 transition-colors">
              {loading ? 'Generating…' : 'Get My Plan →'}
            </button>
          </div>
        ) : (
          <div>
            <div className="space-y-2 text-sm text-gray-700">
              {plan.split('\n').filter(Boolean).map((line, i) => {
                const clean = line.replace(/^[-*]\s*/, '')
                const parts = clean.split(/\*\*(.*?)\*\*/g)
                return (
                  <div key={i} className="flex gap-2 p-2 bg-indigo-50 rounded-lg">
                    <span className="text-indigo-400 mt-0.5">•</span>
                    <p>{parts.map((p, j) => j % 2 === 1 ? <strong key={j}>{p}</strong> : p)}</p>
                  </div>
                )
              })}
            </div>
            <button onClick={() => setPlan(null)} className="mt-4 text-xs text-indigo-500 hover:underline">← Try different inputs</button>
          </div>
        )}
      </div>
    </div>
  )
}

export function UploadZone({ onAnalysed, dark, onToggleDark }: Props) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showManual, setShowManual] = useState(false)

  const handleFile = useCallback(async (file: File) => {
    setError(null)
    setLoading(true)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await fetch('/api/analyse', { method: 'POST', body: form })
      if (!res.ok) {
        const err: ApiError = await res.json()
        setError(err.detail ?? err.error ?? 'Something went wrong')
        return
      }
      const data: AnalysisResponse = await res.json()
      onAnalysed(data)
    } catch {
      setError('Network error — is the backend running?')
    } finally {
      setLoading(false)
    }
  }, [onAnalysed])

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) handleFile(accepted[0])
  }, [handleFile])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    multiple: false,
    disabled: loading,
  })

  return (
    <div className="min-h-screen flex flex-col" style={{ background: dark ? '#0f1117' : '#f5f5f5', transition: 'background 0.2s' }}>
      {/* ET nav */}
      <div className="bg-[#cc0000] text-white px-6 py-2 flex items-center justify-between text-sm">
        <div className="flex items-center gap-3">
          <span className="font-bold text-lg tracking-tight">ET</span>
          <span className="text-red-200">|</span>
          <span className="text-red-100">Economic Times</span>
          <span className="text-red-200 hidden md:inline">|</span>
          <span className="text-red-100 hidden md:inline">Markets</span>
          <span className="text-red-200 hidden md:inline">|</span>
          <span className="text-red-100 hidden md:inline">Wealth</span>
        </div>
        <button onClick={onToggleDark} title={dark ? 'Switch to light mode' : 'Switch to dark mode'}
          style={{ background: 'rgba(255,255,255,0.15)', border: 'none', borderRadius: 20, width: 32, height: 32, cursor: 'pointer', fontSize: 16, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          {dark ? '☀️' : '🌙'}
        </button>
      </div>

      <div className="flex-1 flex items-center justify-center p-6">
      <div className="w-full max-w-lg">
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold text-indigo-700 mb-2">NiveshNetra</h1>
          <p className="text-gray-500 text-lg">Upload your CAMS statement to analyse your portfolio</p>
          <p className="text-xs text-[#cc0000] mt-1 font-medium">ET Money Mentor · Portfolio X-Ray</p>
        </div>

        {/* Drop zone */}
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all
            ${isDragActive
              ? 'border-indigo-500 bg-indigo-50 scale-105'
              : 'border-indigo-300 bg-white hover:border-indigo-500 hover:bg-indigo-50'
            }
            ${loading ? 'opacity-60 cursor-not-allowed' : ''}
          `}
        >
          <input {...getInputProps()} />

          {loading ? (
            <div className="flex flex-col items-center gap-4">
              <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
              <p className="text-indigo-600 font-medium">Analysing your portfolio…</p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-4">
              <div className="text-6xl">📄</div>
              {isDragActive ? (
                <p className="text-indigo-600 font-semibold text-lg">Drop it here!</p>
              ) : (
                <>
                  <p className="text-gray-700 font-semibold text-lg">
                    Drag & drop your CAMS PDF here
                  </p>
                  <p className="text-gray-400 text-sm">or click to browse</p>
                  <p className="text-gray-400 text-xs mt-2">PDF only · max 20 MB</p>
                </>
              )}
            </div>
          )}
        </div>

        {/* Error banner */}
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
            ⚠️ {error}
          </div>
        )}

        {/* No PDF fallback */}
        <div className="mt-6 text-center">
          <p className="text-gray-400 text-sm">Don't have a CAMS statement?</p>
          <button
            onClick={() => setShowManual(true)}
            className="mt-2 text-indigo-600 text-sm font-medium hover:underline"
          >
            Get a quick plan with manual inputs →
          </button>
        </div>

        {/* Footer */}
        <p className="mt-10 text-center text-xs" style={{ color: dark ? '#6b7280' : '#9ca3af' }}>
          Made with ❤️ by <span className="font-semibold" style={{ color: '#cc0000' }}>Shivangi Singh</span>
        </p>
      </div>
      </div>

      {showManual && <ManualPlanModal onClose={() => setShowManual(false)} />}
    </div>
  )
}
