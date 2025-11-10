import { sourceLabels } from "@/lib/utils"
import { Evidence } from "@/lib/types"
import { FileText, Link as LinkIcon, Database } from "lucide-react"

interface SourceBadgeProps {
  source: "page" | "coa" | "api"
  evidence: Evidence
}

export function SourceBadge({ source, evidence }: SourceBadgeProps) {
  const getIcon = () => {
    switch (source) {
      case "coa":
        return <FileText className="h-4 w-4" />
      case "api":
        return <Database className="h-4 w-4" />
      default:
        return <LinkIcon className="h-4 w-4" />
    }
  }

  return (
    <div className="text-sm">
      <div className="flex items-center gap-2 mb-2">
        {getIcon()}
        <span className="font-semibold">Source:</span>
        <span className="text-gray-600">{sourceLabels[source]}</span>
      </div>

      {evidence.coa_lab && (
        <div className="text-xs text-gray-500 ml-6">
          Lab: {evidence.coa_lab}
          {evidence.coa_date && ` • Tested: ${evidence.coa_date}`}
        </div>
      )}

      {evidence.api_source && evidence.match_score !== undefined && (
        <div className="text-xs text-gray-500 ml-6">
          Data from {evidence.api_source} database
          {evidence.match_score < 1.0 && ` (${(evidence.match_score * 100).toFixed(0)}% match)`}
        </div>
      )}
    </div>
  )
}
