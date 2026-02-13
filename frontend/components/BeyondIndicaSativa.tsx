import { sdpCategories } from "@/lib/sdp-categories"

const groups = [
  {
    label: "Sativa",
    description:
      "In SDP research, Orange strains were classified as Sativa nearly 3x more often than expected. Terpinolene — rare across cannabis — dominates these cultivars, producing the uplifting, energetic effects traditionally associated with sativas.",
    categories: ["ORANGE"],
  },
  {
    label: "Modern Indica",
    description:
      "Yellow and Purple strains were both classified as Indica about 30% more often than expected. These represent the modern indica lineage — Kush, OG, Cookies — where Limonene or Caryophyllene leads instead of Myrcene.",
    categories: ["YELLOW", "PURPLE"],
  },
  {
    label: "Classic Indica",
    description:
      "Blue and Green strains also lean Indica, but with a different chemical signature. Blue is Myrcene-dominant (the classic sedating terpene), while Green is Pinene-dominant — rare strains with an alert, focused quality despite Indica heritage.",
    categories: ["BLUE", "GREEN"],
  },
  {
    label: "Hybrid",
    description:
      "Red strains were classified as Hybrid about 40% more often than expected. Their balanced Myrcene/Limonene/Caryophyllene profile maps neatly onto the hybrid experience — versatile effects that borrow from both sides.",
    categories: ["RED"],
  },
]

export function BeyondIndicaSativa() {
  return (
    <div className="space-y-6">
      <div className="bg-card border border-border rounded-lg p-6">
        <p className="text-sm text-foreground/80 leading-relaxed">
          The Strain Data Project analyzed 2,149 observations across 151 strains to see
          how their 6-color Strain Compass correlates with traditional Indica/Sativa/Hybrid
          labels. The result: terpene chemistry explains much of what &quot;Indica&quot; and
          &quot;Sativa&quot; actually mean in practice.
        </p>
      </div>

      {groups.map((group) => (
        <div key={group.label} className="space-y-3">
          <h3 className="font-heading text-lg font-semibold text-foreground">
            {group.label}
          </h3>
          <p className="text-sm text-foreground/70 leading-relaxed">
            {group.description}
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {group.categories.map((key) => {
              const cat = sdpCategories[key]
              if (!cat) return null
              return (
                <div
                  key={key}
                  className="flex items-start gap-3 bg-secondary/30 rounded-lg p-4"
                >
                  <span
                    className="inline-block w-3 h-3 rounded-full shrink-0 mt-0.5"
                    style={{ backgroundColor: cat.color }}
                  />
                  <div className="space-y-1">
                    <p className="text-sm font-semibold text-foreground">
                      {cat.name}{" "}
                      <span className="font-normal text-muted-foreground">
                        — {cat.dominantTerpene}
                      </span>
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {cat.exampleStrains.join(", ")}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      ))}

      <p className="text-center text-xs text-muted-foreground pt-2">
        Based on research from{" "}
        <a
          href="https://straindataproject.org/beyond-indica-and-sativa"
          target="_blank"
          rel="noopener noreferrer"
          className="underline hover:text-primary"
        >
          Strain Data Project
        </a>{" "}
        — 2,149 observations, 151 strains
      </p>
    </div>
  )
}
