import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import type { AnalysisResponse, ApiError } from '../types'

interface Props {
  onAnalysed: (data: AnalysisResponse) => void
}

export function UploadZone({ onAnalysed }: Props) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

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
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-50 flex items-center justify-center p-6">
      <div className="w-full max-w-lg">
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold text-indigo-700 mb-2">NiveshNetra</h1>
          <p className="text-gray-500 text-lg">Upload your CAMS statement to analyse your portfolio</p>
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
      </div>
    </div>
  )
}
