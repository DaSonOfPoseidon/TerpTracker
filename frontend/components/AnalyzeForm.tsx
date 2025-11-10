"use client"

import { useState } from "react"
import { analyzeUrl } from "@/lib/api"
import { AnalysisResult } from "@/lib/types"
import { Button } from "./ui/button"
import { Input } from "./ui/input"
import { Loader2 } from "lucide-react"

interface AnalyzeFormProps {
  onResult: (result: AnalysisResult | null) => void
  loading: boolean
  setLoading: (loading: boolean) => void
}

export function AnalyzeForm({ onResult, loading, setLoading }: AnalyzeFormProps) {
  const [url, setUrl] = useState("")
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    onResult(null)

    try {
      const result = await analyzeUrl(url)
      onResult(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze URL")
      onResult(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
            Enter Strain Product URL
          </label>
          <Input
            id="url"
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/products/strain-name"
            required
            disabled={loading}
            className="w-full"
          />
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
            {error}
          </div>
        )}

        <Button
          type="submit"
          disabled={loading || !url}
          className="w-full"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Analyzing...
            </>
          ) : (
            "Analyze Strain"
          )}
        </Button>
      </form>

      <p className="text-xs text-gray-500 mt-4 text-center">
        Paste a URL to a cannabis product page with terpene information
      </p>
    </div>
  )
}
