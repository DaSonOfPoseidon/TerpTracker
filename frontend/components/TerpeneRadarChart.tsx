"use client"

import dynamic from "next/dynamic"

interface TerpeneRadarChartProps {
  terpenes: Record<string, number>
  categoryColor: string // hex color
}

function formatTerpeneName(name: string): string {
  return name
    .replace(/_/g, "-")
    .replace(/^alpha-/, "\u03b1-")
    .replace(/^beta-/, "\u03b2-")
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

// Lazy-load recharts to avoid SSR issues (recharts uses browser APIs)
const RadarChartInner = dynamic(
  () =>
    import("recharts").then((mod) => {
      const { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer } = mod

      function Chart({ data, categoryColor }: { data: { terpene: string; value: number }[]; categoryColor: string }) {
        return (
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={data} cx="50%" cy="50%" outerRadius="70%">
              <PolarGrid stroke="#e5e7eb" />
              <PolarAngleAxis
                dataKey="terpene"
                tick={{ fontSize: 11, fill: "#4b5563" }}
              />
              <Radar
                dataKey="value"
                stroke={categoryColor}
                fill={categoryColor}
                fillOpacity={0.25}
                strokeWidth={2}
              />
            </RadarChart>
          </ResponsiveContainer>
        )
      }

      return Chart
    }),
  { ssr: false, loading: () => <div className="h-[300px]" /> }
)

export function TerpeneRadarChart({
  terpenes,
  categoryColor,
}: TerpeneRadarChartProps) {
  const entries = Object.entries(terpenes)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)

  // Need at least 3 axes for a radar chart
  if (entries.length < 3) return null

  const maxValue = Math.max(...entries.map(([, v]) => v))
  if (maxValue === 0) return null

  const data = entries.map(([name, value]) => ({
    terpene: formatTerpeneName(name),
    value: (value / maxValue) * 100,
  }))

  return (
    <div className="w-full">
      <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-2 px-6">
        Strain Compass
      </h3>
      <RadarChartInner data={data} categoryColor={categoryColor} />
    </div>
  )
}
