import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { ExperiencePreview } from '@/components/ExperiencePreview'
import type { EffectsAnalysis } from '@/lib/types'

const mockEffects: EffectsAnalysis = {
  overall_character: 'A deeply body-focused experience, best suited for evening',
  onset: '10-20 min',
  peak: '30-50 min',
  duration: '120-180 min',
  best_contexts: ['Nighttime', 'Sleep', 'Pain relief'],
  potential_negatives: ['Drowsiness', 'Couch-lock at high levels'],
  terpene_interactions: [
    'Myrcene and caryophyllene synergize for deep body relaxation',
  ],
  experience_summary: 'Dominated by myrcene with supporting limonene.',
  intensity_estimate: 'High',
  daytime_score: 0.3,
  body_mind_balance: 0.2,
}

describe('ExperiencePreview', () => {
  it('renders the experience summary', () => {
    render(<ExperiencePreview effects={mockEffects} />)
    expect(screen.getByText(/Dominated by myrcene/)).toBeInTheDocument()
  })

  it('renders timeline with onset/peak/duration', () => {
    render(<ExperiencePreview effects={mockEffects} />)
    expect(screen.getByText('10-20 min')).toBeInTheDocument()
    expect(screen.getByText('30-50 min')).toBeInTheDocument()
    expect(screen.getByText('120-180 min')).toBeInTheDocument()
  })

  it('renders best contexts as chips', () => {
    render(<ExperiencePreview effects={mockEffects} />)
    expect(screen.getByText('Nighttime')).toBeInTheDocument()
    expect(screen.getByText('Sleep')).toBeInTheDocument()
    expect(screen.getByText('Pain relief')).toBeInTheDocument()
  })

  it('renders potential negatives warning', () => {
    render(<ExperiencePreview effects={mockEffects} />)
    expect(screen.getByText(/Drowsiness/)).toBeInTheDocument()
    expect(screen.getByText(/Couch-lock/)).toBeInTheDocument()
  })

  it('renders terpene synergies', () => {
    render(<ExperiencePreview effects={mockEffects} />)
    expect(screen.getByText(/synergize/)).toBeInTheDocument()
  })

  it('hides sections with empty arrays', () => {
    const minimal: EffectsAnalysis = {
      ...mockEffects,
      best_contexts: [],
      potential_negatives: [],
      terpene_interactions: [],
    }
    render(<ExperiencePreview effects={minimal} />)
    expect(screen.queryByText('Best for')).not.toBeInTheDocument()
    expect(screen.queryByText('Watch out for')).not.toBeInTheDocument()
    expect(screen.queryByText('Terpene Synergies')).not.toBeInTheDocument()
  })

  it('renders balance meters', () => {
    render(<ExperiencePreview effects={mockEffects} />)
    expect(screen.getByText('Body')).toBeInTheDocument()
    expect(screen.getByText('Mind')).toBeInTheDocument()
    expect(screen.getByText('Night')).toBeInTheDocument()
    expect(screen.getByText('Day')).toBeInTheDocument()
  })
})
