"use client"

import { EffectsAnalysis } from "@/lib/types"
import { Clock, Sun, Moon, AlertTriangle, Zap } from "lucide-react"

interface ExperiencePreviewProps {
  effects: EffectsAnalysis
}

function BalanceMeter({
  value,
  leftLabel,
  rightLabel,
}: {
  value: number
  leftLabel: string
  rightLabel: string
}) {
  const percent = Math.round(value * 100)
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>{leftLabel}</span>
        <span>{rightLabel}</span>
      </div>
      <div className="h-2 bg-secondary rounded-full overflow-hidden">
        <div
          className="h-full bg-primary/70 rounded-full transition-all"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  )
}

export function ExperiencePreview({ effects }: ExperiencePreviewProps) {
  return (
    <div className="px-6 py-4 space-y-5">
      <h3 className="text-sm font-semibold text-botanical-sage uppercase tracking-wide">
        Experience Preview
      </h3>

      {/* Experience Summary */}
      {effects.experience_summary && (
        <p className="text-sm text-foreground/70 italic leading-relaxed">
          {effects.experience_summary}
        </p>
      )}

      {/* Overall Character */}
      {effects.overall_character && (
        <p className="text-sm font-medium text-foreground/90">
          {effects.overall_character}
        </p>
      )}

      {/* Timeline */}
      <div className="grid grid-cols-3 gap-3">
        <div className="text-center p-2.5 bg-secondary/40 rounded-lg">
          <Clock className="h-4 w-4 mx-auto mb-1 text-muted-foreground" />
          <div className="text-xs text-muted-foreground">Onset</div>
          <div className="text-sm font-medium">{effects.onset}</div>
        </div>
        <div className="text-center p-2.5 bg-secondary/40 rounded-lg">
          <Zap className="h-4 w-4 mx-auto mb-1 text-muted-foreground" />
          <div className="text-xs text-muted-foreground">Peak</div>
          <div className="text-sm font-medium">{effects.peak}</div>
        </div>
        <div className="text-center p-2.5 bg-secondary/40 rounded-lg">
          <Sun className="h-4 w-4 mx-auto mb-1 text-muted-foreground" />
          <div className="text-xs text-muted-foreground">Duration</div>
          <div className="text-sm font-medium">{effects.duration}</div>
        </div>
      </div>

      {/* Balance Meters */}
      <div className="space-y-3">
        <BalanceMeter
          value={effects.body_mind_balance}
          leftLabel="Body"
          rightLabel="Mind"
        />
        <BalanceMeter
          value={effects.daytime_score}
          leftLabel="Night"
          rightLabel="Day"
        />
      </div>

      {/* Intensity */}
      {effects.intensity_estimate && effects.intensity_estimate !== "Unknown" && (
        <div className="flex items-center gap-2 text-sm">
          <span className="text-muted-foreground">Intensity:</span>
          <span className="font-medium">{effects.intensity_estimate}</span>
        </div>
      )}

      {/* Best Contexts */}
      {effects.best_contexts.length > 0 && (
        <div>
          <div className="text-xs font-medium text-muted-foreground mb-2">Best for</div>
          <div className="flex flex-wrap gap-1.5">
            {effects.best_contexts.map((ctx) => (
              <span
                key={ctx}
                className="px-2.5 py-1 bg-primary/10 text-primary text-xs rounded-full"
              >
                {ctx}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Potential Negatives */}
      {effects.potential_negatives.length > 0 && (
        <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-md">
          <div className="flex items-center gap-1.5 mb-1.5">
            <AlertTriangle className="h-3.5 w-3.5 text-amber-600" />
            <span className="text-xs font-medium text-amber-700">Watch out for</span>
          </div>
          <ul className="text-xs text-amber-700/80 space-y-0.5">
            {effects.potential_negatives.map((neg) => (
              <li key={neg}>• {neg}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Terpene Synergies */}
      {effects.terpene_interactions.length > 0 && (
        <div>
          <div className="text-xs font-medium text-muted-foreground mb-2">Terpene Synergies</div>
          <div className="space-y-1.5">
            {effects.terpene_interactions.map((interaction) => (
              <div
                key={interaction}
                className="text-xs text-foreground/70 pl-3 border-l-2 border-primary/30"
              >
                {interaction}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
