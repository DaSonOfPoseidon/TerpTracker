"use client"

import { useState } from "react"
import Link from "next/link"
import { AnalyzeForm } from "@/components/AnalyzeForm"
import { ResultCard } from "@/components/ResultCard"
import { AnalysisResult } from "@/lib/types"
import { BookOpen } from "lucide-react"

export default function Home() {
  const [result, setResult] = useState<AnalysisResult | null>(null)

  return (
    <main className="container mx-auto px-4 py-12 max-w-4xl">
      <header className="text-center mb-12">
        <h1 className="font-heading text-5xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
          TerpTracker
        </h1>
        <p className="text-lg text-foreground/80 mb-2">
          Analyze cannabis strain terpene profiles and discover their SDP category
        </p>
        <p className="text-sm text-muted-foreground">
          Multi-source data merging from COAs, databases, and APIs
        </p>
      </header>

      <AnalyzeForm onResult={setResult} />

      {result && (
        <div className="mt-8 animate-fade-in-up">
          <ResultCard result={result} />
        </div>
      )}

      <div className="mt-12 text-center">
        <Link
          href="/learn"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-primary transition-colors"
        >
          <BookOpen className="h-4 w-4" />
          Learn about terpenes and SDP categories
        </Link>
      </div>
    </main>
  )
}
