import type { Metadata } from "next"
import { BeyondIndicaSativa } from "@/components/BeyondIndicaSativa"
import { SDPGuide } from "@/components/SDPGuide"
import { TerpenePanel } from "@/components/TerpenePanel"

export const metadata: Metadata = {
  title: "Learn - TerpTracker",
  description: "Learn about SDP terpene categories and individual terpene profiles",
}

export default function LearnPage() {
  return (
    <main className="container mx-auto px-4 py-10 max-w-4xl">
      <header className="mb-10">
        <h1 className="font-heading text-4xl font-bold text-foreground mb-2">
          Cannabis Terpene Guide
        </h1>
        <p className="text-muted-foreground">
          Understand the six SDP categories and what each terpene does.
        </p>
      </header>

      <section className="mb-10">
        <h2 className="font-heading text-2xl font-semibold text-foreground mb-4">
          Beyond Indica &amp; Sativa
        </h2>
        <p className="text-muted-foreground mb-4">
          How terpene chemistry maps to the labels you already know.
        </p>
        <BeyondIndicaSativa />
      </section>

      <hr className="leaf-divider my-10" />

      <section className="mb-10">
        <h2 className="font-heading text-2xl font-semibold text-foreground mb-4">
          SDP Categories
        </h2>
        <SDPGuide />
      </section>

      <hr className="leaf-divider my-10" />

      <section>
        <h2 className="font-heading text-2xl font-semibold text-foreground mb-4">
          Terpene Glossary
        </h2>
        <div className="bg-card border border-border rounded-lg p-6">
          <TerpenePanel />
        </div>
      </section>
    </main>
  )
}
