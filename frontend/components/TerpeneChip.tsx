import { formatPercent } from "@/lib/utils"

interface TerpeneChipProps {
  name: string
  value: number
}

export function TerpeneChip({ name, value }: TerpeneChipProps) {
  const displayName = name
    .replace(/_/g, "-")
    .replace(/^alpha-/, "\u03b1-")
    .replace(/^beta-/, "\u03b2-")

  return (
    <div className="inline-flex items-center gap-2 bg-botanical-leaf/15 text-botanical-sage border border-botanical-leaf/25 px-3 py-1 rounded-full text-sm font-medium">
      <span className="capitalize">{displayName}</span>
      <span className="font-bold text-foreground">{formatPercent(value)}</span>
    </div>
  )
}
