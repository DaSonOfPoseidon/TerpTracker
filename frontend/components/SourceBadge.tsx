import { sourceLabels } from "@/lib/utils"
import { Evidence } from "@/lib/types"
import { FileText, Link as LinkIcon, Database, Globe } from "lucide-react"

interface SourceBadgeProps {
  sources?: string[]
  source?: string // legacy fallback
  evidence: Evidence
}

function getIcon(src: string) {
  switch (src) {
    case "coa":
      return <FileText className="h-4 w-4" />
    case "api":
      return <Globe className="h-4 w-4" />
    case "database":
      return <Database className="h-4 w-4" />
    default:
      return <LinkIcon className="h-4 w-4" />
  }
}

function formatRelativeTime(dateStr: string): string {
  const cached = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - cached.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1) return "just now"
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d ago`
}

export function SourceBadge({ sources, source, evidence }: SourceBadgeProps) {
  // Resolve to array, falling back to legacy single source
  const sourceList = sources ?? (source ? [source] : [])

  return (
    <div className="text-sm space-y-2">
      <div className="flex flex-wrap items-center gap-3">
        <span className="font-semibold text-gray-700">Sources:</span>
        {sourceList.map((src) => (
          <span
            key={src}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gray-100 text-gray-700 text-xs font-medium"
          >
            {getIcon(src)}
            {sourceLabels[src] || src}
          </span>
        ))}
      </div>

      {evidence.coa_lab && (
        <div className="text-xs text-gray-500 ml-1">
          Lab: {evidence.coa_lab}
          {evidence.coa_date && ` \u2022 Tested: ${evidence.coa_date}`}
        </div>
      )}

      {evidence.api_source && (
        <div className="text-xs text-gray-500 ml-1">
          Data from {evidence.api_source} database
          {evidence.match_score !== undefined && evidence.match_score < 1.0 && (
            <span className="ml-1 px-1.5 py-0.5 rounded bg-yellow-50 text-yellow-700 font-medium">
              {(evidence.match_score * 100).toFixed(0)}% match
            </span>
          )}
        </div>
      )}

      {evidence.cached_at && (
        <div className="text-xs text-gray-400 ml-1">
          Cached {formatRelativeTime(evidence.cached_at)}
        </div>
      )}
    </div>
  )
}
