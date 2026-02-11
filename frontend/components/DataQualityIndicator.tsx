import { FlaskConical, Pill, FileCheck } from "lucide-react"
import { DataAvailability } from "@/lib/types"

interface DataQualityIndicatorProps {
  data: DataAvailability
}

export function DataQualityIndicator({ data }: DataQualityIndicatorProps) {
  return (
    <div className="flex flex-wrap items-center gap-3 text-xs">
      {data.has_terpenes && (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-green-50 text-green-700">
          <FlaskConical className="h-3 w-3" />
          {data.terpene_count} terpenes
        </span>
      )}
      {data.has_cannabinoids && (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-blue-50 text-blue-700">
          <Pill className="h-3 w-3" />
          {data.cannabinoid_count} cannabinoids
        </span>
      )}
      {data.has_coa && (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-purple-50 text-purple-700">
          <FileCheck className="h-3 w-3" />
          COA verified
        </span>
      )}
    </div>
  )
}
