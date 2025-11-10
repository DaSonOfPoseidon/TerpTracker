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

  useEffect(() => {
    listTerpenes()
      .then(setTerpenes)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="text-sm text-gray-500">Loading terpene information...</div>
  }

  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">
        Learn More About Terpenes
      </h3>

      <Accordion type="single" collapsible className="w-full">
        {terpenes.map((terpene) => (
          <AccordionItem key={terpene.key} value={terpene.key}>
            <AccordionTrigger className="text-sm font-medium">
              {terpene.name}
            </AccordionTrigger>
            <AccordionContent>
              <div className="space-y-2 text-sm text-gray-700">
                {terpene.description && <p>{terpene.description}</p>}

                {terpene.aroma && (
                  <div>
                    <span className="font-semibold">Aroma:</span> {terpene.aroma}
                  </div>
                )}

                {terpene.effects && terpene.effects.length > 0 && (
                  <div>
                    <span className="font-semibold">Effects:</span>{" "}
                    {terpene.effects.join(", ")}
                  </div>
                )}

                {terpene.also_found_in && terpene.also_found_in.length > 0 && (
                  <div>
                    <span className="font-semibold">Also found in:</span>{" "}
                    {terpene.also_found_in.join(", ")}
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
