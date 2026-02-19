import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { ResultCard } from '@/components/ResultCard'
import type { AnalysisResult } from '@/lib/types'

// Mock next/link since we're outside Next.js
vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}))

// Mock recharts to avoid canvas issues in jsdom
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  RadarChart: ({ children }: any) => <div>{children}</div>,
  Radar: () => <div />,
  PolarGrid: () => <div />,
  PolarAngleAxis: () => <div />,
  PolarRadiusAxis: () => <div />,
}))

const mockResult: AnalysisResult = {
  sources: ['page', 'database'],
  terpenes: { myrcene: 0.35, limonene: 0.25, caryophyllene: 0.15 },
  totals: { thc: 0.20, thca: 0.22, total_terpenes: 0.021 },
  category: 'BLUE',
  traditional_label: 'Classic Indica',
  summary: 'Blue Dream is myrcene-forward with an earthy, relaxing profile.',
  strain_guess: 'Blue Dream',
  evidence: { detection_method: 'page_scrape', url: 'https://example.com' },
  data_available: {
    has_terpenes: true,
    has_cannabinoids: true,
    has_coa: false,
    terpene_count: 3,
    cannabinoid_count: 2,
  },
  cannabinoid_insights: ['THC-dominant, minimal CBD', 'High potency'],
}

describe('ResultCard', () => {
  it('renders the strain name', () => {
    render(<ResultCard result={mockResult} />)
    expect(screen.getByText('Blue Dream')).toBeInTheDocument()
  })

  it('renders the SDP category badge', () => {
    render(<ResultCard result={mockResult} />)
    expect(screen.getByText('BLUE')).toBeInTheDocument()
  })

  it('renders the summary text', () => {
    render(<ResultCard result={mockResult} />)
    expect(screen.getByText(/myrcene-forward/)).toBeInTheDocument()
  })

  it('renders terpene chips', () => {
    render(<ResultCard result={mockResult} />)
    // TerpeneChip components should render terpene names
    expect(screen.getByText(/myrcene/i)).toBeInTheDocument()
  })

  it('renders cannabinoid insights', () => {
    render(<ResultCard result={mockResult} />)
    expect(screen.getByText(/THC-dominant/)).toBeInTheDocument()
    expect(screen.getByText(/High potency/)).toBeInTheDocument()
  })

  it('renders totals section', () => {
    render(<ResultCard result={mockResult} />)
    expect(screen.getByText('Totals')).toBeInTheDocument()
  })

  it('renders the SDP attribution footer', () => {
    render(<ResultCard result={mockResult} />)
    expect(screen.getByText(/Strain Data Project/)).toBeInTheDocument()
  })

  it('renders without crashing when minimal data', () => {
    const minimal: AnalysisResult = {
      sources: ['page'],
      terpenes: { myrcene: 0.5 },
      totals: {},
      category: 'BLUE',
      summary: 'Minimal data',
      strain_guess: 'Unknown',
      evidence: { detection_method: 'page_scrape' },
    }
    render(<ResultCard result={minimal} />)
    expect(screen.getByText('Unknown')).toBeInTheDocument()
  })
})
