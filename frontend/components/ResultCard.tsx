"use client"

import Link from "next/link"
import { AnalysisResult } from "@/lib/types"
import { categoryColors, formatPercent } from "@/lib/utils"
import { sdpCategories } from "@/lib/sdp-categories"
import { TerpeneChip } from "./TerpeneChip"
import { SourceBadge } from "./SourceBadge"
import { TerpeneRadarChart } from "./TerpeneRadarChart"
import { DataQualityIndicator } from "./DataQualityIndicator"
import { CannabinoidInsights } from "./CannabinoidInsights"
import { ExperiencePreview } from "./ExperiencePreview"
import { BookOpen } from "lucide-react"

interface ResultCardProps {
  result: AnalysisResult
}

function StatField({ label, value }: { label: string; value: number | undefined }) {
  if (value === undefined) return null
  return (
    <div>
      <span className="text-muted-foreground">{label}:</span>{" "}
      <span className="font-semibold">{formatPercent(value)}</span>
    </div>
  )
}

export function ResultCard({ result }: ResultCardProps) {
  const categoryColor = categoryColors[result.category]
  const sdp = sdpCategories[result.category]

  return (
    <div className="bg-card border border-border rounded-lg overflow-hidden">
      {/* Header with category */}
      <div className={`${categoryColor} px-6 py-4`}>
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">{result.strain_guess}</h2>
          <span className="text-sm font-medium px-3 py-1 bg-black/20 rounded-full">
            {result.category}
          </span>
        </div>
      </div>

      {/* Traditional Label + Insight */}
      {sdp && (
        <div className="px-6 py-3 flex flex-wrap items-center gap-3 bg-secondary/20">
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-foreground/10 text-foreground/70">
            {sdp.traditionalLabel}
          </span>
          <span className="text-xs text-muted-foreground italic">
            Think: {sdp.exampleStrains.join(", ")}
          </span>
          <span className="hidden sm:inline text-xs text-muted-foreground">
            — {sdp.experienceDescription}
          </span>
        </div>
      )}

      {/* Summary */}
      <div className="px-6 py-4">
        <p className="text-foreground/80 leading-relaxed">{result.summary}</p>
      </div>
      <hr className="leaf-divider" />

      {/* Experience Preview */}
      {result.effects && (
        <>
          <ExperiencePreview effects={result.effects} />
          <hr className="leaf-divider" />
        </>
      )}

      {/* Terpenes */}
      <div className="px-6 py-4">
        <h3 className="text-sm font-semibold text-botanical-sage uppercase tracking-wide mb-3">
          Terpene Profile
        </h3>
        <div className="flex flex-wrap gap-2">
          {Object.entries(result.terpenes)
            .sort((a, b) => b[1] - a[1])
            .map(([name, value]) => (
              <TerpeneChip key={name} name={name} value={value} />
            ))}
        </div>
      </div>
      <hr className="leaf-divider" />

      {/* Radar Chart */}
      {sdp && (
        <>
          <div className="py-4">
            <TerpeneRadarChart
              terpenes={result.terpenes}
              categoryColor={sdp.color}
            />
          </div>
          <hr className="leaf-divider" />
        </>
      )}

      {/* Totals */}
      <div className="px-6 py-4 bg-secondary/30">
        <h3 className="text-sm font-semibold text-botanical-sage uppercase tracking-wide mb-3">
          Totals
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          <StatField label="Total Terpenes" value={result.totals.total_terpenes} />
          <StatField label="THC" value={result.totals.thc} />
          <StatField label="THCa" value={result.totals.thca} />
          <StatField label="CBD" value={result.totals.cbd} />
        </div>

        {result.totals.total_terpenes !== undefined && result.totals.thca !== undefined && (
          <div className="mt-4 p-3 bg-botanical-leaf/15 border border-botanical-leaf/25 rounded-md">
            <p className="text-xs text-botanical-sage">
              <span className="font-semibold">Rosin-ability (experimental):</span> This strain
              shows {formatPercent(result.totals.total_terpenes)} total terpenes and{" "}
              {formatPercent(result.totals.thca)} THCa. Higher values may indicate better rosin
              potential, but this is not a guarantee.
            </p>
          </div>
        )}
      </div>
      <hr className="leaf-divider" />

      {/* Cannabinoid Insights */}
      {result.cannabinoid_insights && result.cannabinoid_insights.length > 0 && (
        <>
          <CannabinoidInsights insights={result.cannabinoid_insights} />
          <hr className="leaf-divider" />
        </>
      )}

      {/* Source + Data Quality */}
      <div className="px-6 py-4 space-y-3">
        <SourceBadge
          sources={result.sources}
          source={result.source}
          evidence={result.evidence}
        />
        {result.data_available && (
          <DataQualityIndicator data={result.data_available} />
        )}
      </div>
      <hr className="leaf-divider" />

      {/* SDP Attribution Footer */}
      <div className="px-6 py-3 text-center flex items-center justify-center gap-4">
        <p className="text-xs text-muted-foreground">
          Classification by{" "}
          <a
            href="https://straindataproject.org/"
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-primary"
          >
            Strain Data Project
          </a>
        </p>
        <Link
          href="/learn"
          className="inline-flex items-center gap-1 text-xs text-primary hover:text-primary/80 transition-colors"
        >
          <BookOpen className="h-3 w-3" />
          Learn more
        </Link>
      </div>
    </div>
  )
}
