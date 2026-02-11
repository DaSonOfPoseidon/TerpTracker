"use client"

import { useState, useEffect } from "react"
import { listTerpenes } from "@/lib/api"
import { TerpeneInfo } from "@/lib/types"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"

export function TerpenePanel() {
  const [terpenes, setTerpenes] = useState<TerpeneInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    listTerpenes()
      .then(setTerpenes)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load terpene info"))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="text-sm text-muted-foreground">Loading terpene information...</div>
  }

  if (error) {
    return <div className="text-sm text-destructive">Failed to load terpene information: {error}</div>
  }

  return (
    <div>
      <h3 className="text-sm font-semibold text-botanical-sage uppercase tracking-wide mb-3">
        Learn More About Terpenes
      </h3>

      <Accordion type="single" collapsible className="w-full">
        {terpenes.map((terpene) => (
          <AccordionItem key={terpene.key} value={terpene.key}>
            <AccordionTrigger className="text-sm font-medium">
              {terpene.name}
            </AccordionTrigger>
            <AccordionContent>
              <div className="space-y-2 text-sm text-foreground/80">
                {terpene.description && <p>{terpene.description}</p>}

                {terpene.aroma && (
                  <div>
                    <span className="font-semibold text-foreground">Aroma:</span>{" "}
                    <span className="text-muted-foreground">{terpene.aroma}</span>
                  </div>
                )}

                {terpene.effects && terpene.effects.length > 0 && (
                  <div>
                    <span className="font-semibold text-foreground">Effects:</span>{" "}
                    <span className="text-muted-foreground">{terpene.effects.join(", ")}</span>
                  </div>
                )}

                {terpene.also_found_in && terpene.also_found_in.length > 0 && (
                  <div>
                    <span className="font-semibold text-foreground">Also found in:</span>{" "}
                    <span className="text-muted-foreground">{terpene.also_found_in.join(", ")}</span>
                  </div>
                )}
              </div>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </div>
  )
}
