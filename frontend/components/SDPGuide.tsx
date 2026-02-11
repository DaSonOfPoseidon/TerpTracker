import { sdpCategories } from "@/lib/sdp-categories"

export function SDPGuide() {
  const categories = Object.entries(sdpCategories)

  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {categories.map(([key, cat]) => (
          <div
            key={key}
            className="bg-card border border-border rounded-lg p-5 space-y-2"
          >
            <div className="flex items-center gap-3">
              <span
                className="inline-block w-3.5 h-3.5 rounded-full shrink-0"
                style={{ backgroundColor: cat.color }}
              />
              <h3 className="font-heading text-lg font-semibold text-foreground">
                {cat.name}
              </h3>
            </div>
            <p className="text-sm text-foreground/80">{cat.description}</p>
            <p className="text-xs text-muted-foreground">{cat.secondaryNotes}</p>
            <p className="text-xs text-botanical-sage">
              Dominant: {cat.dominantTerpene}
            </p>
          </div>
        ))}
      </div>

      <p className="mt-6 text-center text-xs text-muted-foreground">
        Classification system by{" "}
        <a
          href="https://straindataproject.org/"
          target="_blank"
          rel="noopener noreferrer"
          className="underline hover:text-primary"
        >
          Strain Data Project
        </a>
      </p>
    </div>
  )
}
