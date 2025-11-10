"use client"

import { useState } from "react"
import { AnalyzeForm } from "@/components/AnalyzeForm"
import { ResultCard } from "@/components/ResultCard"
import { AnalysisResult } from "@/lib/types"

export default function Home() {
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [loading, setLoading] = useState(false)

  return (
    <main className="container mx-auto px-4 py-8 max-w-4xl">
      <header className="text-center mb-12">
        <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
          TerpTracker
        </h1>
        <p className="text-lg text-gray-600">
          Analyze cannabis strain terpene profiles and discover their SDP category
        </p>
      </header>

      <AnalyzeForm
        onResult={setResult}
        loading={loading}
        setLoading={setLoading}
      />

      {result && (
        <div className="mt-8">
          <ResultCard result={result} />
        </div>
      )}
    </main>
  )
}
