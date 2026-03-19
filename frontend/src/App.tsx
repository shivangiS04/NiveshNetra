import { useState } from 'react'
import { Dashboard } from './components/Dashboard'
import { UploadZone } from './components/UploadZone'
import type { AnalysisResponse } from './types'

export default function App() {
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null)

  return analysis
    ? <Dashboard data={analysis} onReset={() => setAnalysis(null)} />
    : <UploadZone onAnalysed={setAnalysis} />
}
