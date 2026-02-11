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
  const sourceList = sources ?? (source ? [source] : [])

  return (
    <div className="text-sm space-y-2">
      <div className="flex flex-wrap items-center gap-3">
        <span className="font-semibold text-foreground/70">Sources:</span>
        {sourceList.map((src) => (
          <span
            key={src}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-secondary text-secondary-foreground text-xs font-medium"
          >
            {getIcon(src)}
            {sourceLabels[src] || src}
          </span>
        ))}
      </div>

      {evidence.coa_lab && (
        <div className="text-xs text-muted-foreground ml-1">
          Lab: {evidence.coa_lab}
          {evidence.coa_date && ` \u2022 Tested: ${evidence.coa_date}`}
        </div>
      )}

      {evidence.api_source && (
        <div className="text-xs text-muted-foreground ml-1">
          Data from {evidence.api_source} database
          {evidence.match_score !== undefined && evidence.match_score < 1.0 && (
            <span className="ml-1 px-1.5 py-0.5 rounded bg-botanical-amber/15 text-botanical-amber font-medium">
              {(evidence.match_score * 100).toFixed(0)}% match
            </span>
          )}
        </div>
      )}

      {evidence.cached_at && (
        <div className="text-xs text-muted-foreground/60 ml-1">
          Cached {formatRelativeTime(evidence.cached_at)}
        </div>
      )}
    </div>
  )
}
