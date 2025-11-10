import { describe, it, expect } from 'vitest'
import type { AnalysisResult, TerpeneProfile, Totals } from '@/lib/types'

describe('Type definitions', () => {
  it('should accept valid AnalysisResult', () => {
    const validResult: AnalysisResult = {
      source: 'page',
      terpenes: { myrcene: 0.5, limonene: 0.3 },
      totals: { total_terpenes: 2.1 },
      category: 'BLUE',
      summary: 'Test summary',
      strain_guess: 'Test Strain',
      evidence: {
        detection_method: 'page_scrape',
        url: 'https://example.com'
      }
    }

    expect(validResult.source).toBe('page')
    expect(validResult.category).toBe('BLUE')
  })

  it('should accept valid TerpeneProfile', () => {
    const profile: TerpeneProfile = {
      myrcene: 0.5,
      limonene: 0.3,
      caryophyllene: 0.2
    }

    expect(Object.keys(profile)).toHaveLength(3)
    expect(profile.myrcene).toBe(0.5)
  })

  it('should accept valid Totals with optional fields', () => {
    const totals: Totals = {
      total_terpenes: 2.1,
      thca: 25.0
    }

    expect(totals.total_terpenes).toBe(2.1)
    expect(totals.thca).toBe(25.0)
    expect(totals.thc).toBeUndefined()
  })
})
