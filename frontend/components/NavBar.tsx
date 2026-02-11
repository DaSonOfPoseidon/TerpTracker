"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Leaf } from "lucide-react"

export function NavBar() {
  const pathname = usePathname()

  const links = [
    { href: "/", label: "Analyze" },
    { href: "/learn", label: "Learn" },
  ]

  return (
    <nav className="sticky top-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-sm">
      <div className="container mx-auto max-w-4xl flex items-center justify-between px-4 h-14">
        <Link href="/" className="flex items-center gap-2 text-primary hover:opacity-80 transition-opacity">
          <Leaf className="h-5 w-5" />
          <span className="font-heading text-lg font-semibold tracking-wide">TerpTracker</span>
        </Link>

        <div className="flex items-center gap-6">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`text-sm font-medium transition-colors ${
                pathname === link.href
                  ? "text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {link.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  )
}
