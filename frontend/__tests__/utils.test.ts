import { describe, it, expect } from 'vitest'
import { categoryColors, sourceLabels, formatPercent } from '@/lib/utils'

describe('Utils', () => {
  describe('categoryColors', () => {
    it('should have color classes for all SDP categories', () => {
      const categories = ['BLUE', 'YELLOW', 'PURPLE', 'GREEN', 'ORANGE', 'RED']
      categories.forEach(category => {
        expect(categoryColors[category as keyof typeof categoryColors]).toBeDefined()
        expect(categoryColors[category as keyof typeof categoryColors]).toContain('bg-')
      })
    })
  })

  describe('sourceLabels', () => {
    it('should have labels for all source types', () => {
      expect(sourceLabels.page).toBe('On-page data')
      expect(sourceLabels.coa).toBe('Certificate of Analysis')
      expect(sourceLabels.api).toBe('Strain database')
    })
  })

  describe('formatPercent', () => {
    it('should format decimal values as percentages', () => {
      expect(formatPercent(0.5)).toBe('50.00%')
      expect(formatPercent(0.123)).toBe('12.30%')
      expect(formatPercent(1.0)).toBe('100.00%')
    })

    it('should handle undefined and null values', () => {
      expect(formatPercent(undefined)).toBe('N/A')
      expect(formatPercent(null as any)).toBe('N/A')
    })

    it('should handle very small values', () => {
      expect(formatPercent(0.001)).toBe('0.10%')
      expect(formatPercent(0.0001)).toBe('0.01%')
    })
  })
})
