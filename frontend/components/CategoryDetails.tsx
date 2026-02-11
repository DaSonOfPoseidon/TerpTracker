import { sdpCategories } from "@/lib/sdp-categories"

interface CategoryDetailsProps {
  category: string
  terpenes: Record<string, number>
}

function formatTerpeneName(name: string): string {
  return name
    .replace(/_/g, "-")
    .replace(/^alpha-/, "\u03b1-")
    .replace(/^beta-/, "\u03b2-")
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

export function CategoryDetails({ category, terpenes }: CategoryDetailsProps) {
  const sdp = sdpCategories[category]
  if (!sdp) return null

  // Find the top terpene for the "why" explanation
  const sorted = Object.entries(terpenes).sort((a, b) => b[1] - a[1])
  const topTerpene = sorted[0]

  return (
    <div className="px-6 py-4 border-b">
      <div className="flex items-start gap-3">
        <div
          className="w-4 h-4 rounded-full mt-1 shrink-0"
          style={{ backgroundColor: sdp.color }}
        />
        <div className="space-y-1">
          <h3 className="font-semibold text-gray-900">
            SDP {sdp.name} &mdash; {sdp.description}
          </h3>
          <p className="text-sm text-gray-600">{sdp.secondaryNotes}</p>
          {topTerpene && (
            <p className="text-xs text-gray-500">
              This strain&apos;s top terpene is{" "}
              <span className="font-medium">
                {formatTerpeneName(topTerpene[0])}
              </span>{" "}
              at {(topTerpene[1] * 100).toFixed(1)}%
            </p>
          )}
          <p className="text-xs text-gray-400 pt-1">
            Classification by{" "}
            <a
              href="https://straindataproject.org/"
              target="_blank"
              rel="noopener noreferrer"
              className="underline hover:text-gray-600"
            >
              Strain Data Project
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}
