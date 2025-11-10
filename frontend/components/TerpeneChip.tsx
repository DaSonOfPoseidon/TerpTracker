import { formatPercent } from "@/lib/utils"

interface TerpeneChipProps {
  name: string
  value: number
}

export function TerpeneChip({ name, value }: TerpeneChipProps) {
  // Format name for display
  const displayName = name
    .replace(/_/g, "-")
    .replace(/^alpha-/, "α-")
    .replace(/^beta-/, "β-")

  return (
    <div className="inline-flex items-center gap-2 bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium">
      <span className="capitalize">{displayName}</span>
      <span className="font-bold">{formatPercent(value)}</span>
    </div>
  )
}
