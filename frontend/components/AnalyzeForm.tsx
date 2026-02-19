"use client"

import { useState } from "react"
import { analyzeUrl } from "@/lib/api"
import { AnalysisResult } from "@/lib/types"
import { StrainSearchInput } from "./StrainSearchInput"
import { Button } from "./ui/button"
import { Input } from "./ui/input"
import { Loader2, Search, Link, Leaf } from "lucide-react"

type Mode = "url" | "strain"

interface AnalyzeFormProps {
  onResult: (result: AnalysisResult | null) => void
}

export function AnalyzeForm({ onResult }: AnalyzeFormProps) {
  const [mode, setMode] = useState<Mode>("strain")
  const [url, setUrl] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleUrlSubmit = async (e: React.FormEvent) => {
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
    <div className="bg-card border border-border rounded-lg p-6 hero-glow">
      {/* Mode Toggle */}
      <div className="flex gap-1 mb-4 p-1 bg-secondary/50 rounded-lg">
        <button
          type="button"
          onClick={() => setMode("strain")}
          className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
            mode === "strain"
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          <Leaf className="h-4 w-4" />
          Strain Name
        </button>
        <button
          type="button"
          onClick={() => setMode("url")}
          className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
            mode === "url"
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          <Link className="h-4 w-4" />
          Product URL
        </button>
      </div>

      {mode === "strain" ? (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-2">
              Search by Strain Name
            </label>
            <StrainSearchInput onResult={onResult} />
          </div>
          <p className="text-xs text-muted-foreground text-center">
            Search our database of 50,000+ strain profiles
          </p>
        </div>
      ) : (
        <form onSubmit={handleUrlSubmit} className="space-y-4">
          <div>
            <label htmlFor="url" className="block text-sm font-medium text-muted-foreground mb-2">
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
            <div className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-md text-sm">
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
              <>
                <Search className="mr-2 h-4 w-4" />
                Analyze Strain
              </>
            )}
          </Button>

          <p className="text-xs text-muted-foreground text-center">
            Paste a URL to a cannabis product page with terpene information
          </p>
        </form>
      )}
    </div>
  )
}
