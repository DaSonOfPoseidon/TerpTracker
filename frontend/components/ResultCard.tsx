"use client"

import { AnalysisResult } from "@/lib/types"
import { categoryColors, sourceLabels, formatPercent } from "@/lib/utils"
import { TerpeneChip } from "./TerpeneChip"
import { SourceBadge } from "./SourceBadge"
import { TerpenePanel } from "./TerpenePanel"

interface ResultCardProps {
  result: AnalysisResult
}

export function ResultCard({ result }: ResultCardProps) {
  const categoryColor = categoryColors[result.category]

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header with category */}
      <div className={`${categoryColor} px-6 py-4`}>
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">{result.strain_guess}</h2>
          <span className="text-sm font-medium px-3 py-1 bg-white/20 rounded-full">
            {result.category}
          </span>
        </div>
      </div>

      {/* Summary */}
      <div className="px-6 py-4 border-b">
        <p className="text-gray-700 leading-relaxed">{result.summary}</p>
      </div>

      {/* Terpenes */}
      <div className="px-6 py-4 border-b">
        <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">
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

      {/* Totals */}
      <div className="px-6 py-4 border-b bg-gray-50">
        <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">
          Totals
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          {result.totals.total_terpenes !== undefined && (
            <div>
              <span className="text-gray-600">Total Terpenes:</span>{" "}
              <span className="font-semibold">{formatPercent(result.totals.total_terpenes)}</span>
            </div>
          )}
          {result.totals.thc !== undefined && (
            <div>
              <span className="text-gray-600">THC:</span>{" "}
              <span className="font-semibold">{formatPercent(result.totals.thc)}</span>
            </div>
          )}
          {result.totals.thca !== undefined && (
            <div>
              <span className="text-gray-600">THCa:</span>{" "}
              <span className="font-semibold">{formatPercent(result.totals.thca)}</span>
            </div>
          )}
          {result.totals.cbd !== undefined && (
            <div>
              <span className="text-gray-600">CBD:</span>{" "}
              <span className="font-semibold">{formatPercent(result.totals.cbd)}</span>
            </div>
          )}
        </div>

        {result.totals.total_terpenes !== undefined && result.totals.thca !== undefined && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
            <p className="text-xs text-blue-900">
              <span className="font-semibold">Rosin-ability (experimental):</span> This strain
              shows {formatPercent(result.totals.total_terpenes)} total terpenes and{" "}
              {formatPercent(result.totals.thca)} THCa. Higher values may indicate better rosin
              potential, but this is not a guarantee.
            </p>
          </div>
        )}
      </div>

      {/* Source */}
      <div className="px-6 py-4">
        <SourceBadge source={result.source} evidence={result.evidence} />
      </div>

      {/* Learn More */}
      <div className="px-6 py-4 border-t bg-gray-50">
        <TerpenePanel />
      </div>
    </div>
  )
}
