import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "TerpTracker - Cannabis Terpene Profile Analyzer",
  description: "Analyze cannabis strain terpene profiles and get SDP category classifications",
  manifest: "/manifest.json",
  themeColor: "#10B981",
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
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
          {children}
        </div>
      </body>
    </html>
  )
}
