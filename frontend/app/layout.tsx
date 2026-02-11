import type { Metadata } from "next"
import { Cormorant_Garamond, Source_Sans_3 } from "next/font/google"
import { NavBar } from "@/components/NavBar"
import "./globals.css"

const cormorant = Cormorant_Garamond({
  subsets: ["latin"],
  weight: ["400", "600", "700"],
  variable: "--font-cormorant",
  display: "swap",
})

const sourceSans = Source_Sans_3({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-source-sans",
  display: "swap",
})

export const metadata: Metadata = {
  title: "TerpTracker - Cannabis Terpene Profile Analyzer",
  description: "Analyze cannabis strain terpene profiles and get SDP category classifications",
  manifest: "/manifest.json",
  themeColor: "#121916",
  viewport: {
    width: "device-width",
    initialScale: 1,
    maximumScale: 1,
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${cormorant.variable} ${sourceSans.variable}`}>
      <body>
        <div className="botanical-bg">
          <NavBar />
          {children}
        </div>
      </body>
    </html>
  )
}
