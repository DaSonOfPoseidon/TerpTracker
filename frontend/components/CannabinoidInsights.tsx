interface CannabinoidInsightsProps {
  insights: string[]
}

export function CannabinoidInsights({ insights }: CannabinoidInsightsProps) {
  if (!insights.length) return null

  return (
    <div className="px-6 py-4 border-b">
      <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">
        Cannabinoid Insights
      </h3>
      <div className="flex flex-wrap gap-2">
        {insights.map((insight) => (
          <span
            key={insight}
            className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-amber-50 text-amber-800 border border-amber-200"
          >
            {insight}
          </span>
        ))}
      </div>
    </div>
  )
}
