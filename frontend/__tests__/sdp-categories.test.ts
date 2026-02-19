import { describe, it, expect } from 'vitest'
import { sdpCategories } from '@/lib/sdp-categories'

describe('SDP Categories', () => {
  const allCategories = ['BLUE', 'YELLOW', 'PURPLE', 'GREEN', 'ORANGE', 'RED']

  it('should define all 6 SDP categories', () => {
    allCategories.forEach(cat => {
      expect(sdpCategories[cat]).toBeDefined()
    })
  })

  it('should have required fields on each category', () => {
    allCategories.forEach(cat => {
      const sdp = sdpCategories[cat]
      expect(sdp.name).toBeTruthy()
      expect(sdp.dominantTerpene).toBeTruthy()
      expect(sdp.description).toBeTruthy()
      expect(sdp.color).toMatch(/^#[0-9a-f]{6}$/)
      expect(sdp.traditionalLabel).toBeTruthy()
      expect(sdp.exampleStrains.length).toBeGreaterThan(0)
      expect(sdp.experienceDescription).toBeTruthy()
    })
  })

  it('should have correct traditional labels per SDP research', () => {
    expect(sdpCategories.ORANGE.traditionalLabel).toBe('Sativa')
    expect(sdpCategories.YELLOW.traditionalLabel).toBe('Modern Indica')
    expect(sdpCategories.PURPLE.traditionalLabel).toBe('Modern Indica')
    expect(sdpCategories.GREEN.traditionalLabel).toBe('Classic Indica')
    expect(sdpCategories.BLUE.traditionalLabel).toBe('Classic Indica')
    expect(sdpCategories.RED.traditionalLabel).toBe('Hybrid')
  })

  it('should have unique colors for each category', () => {
    const colors = allCategories.map(cat => sdpCategories[cat].color)
    const uniqueColors = new Set(colors)
    expect(uniqueColors.size).toBe(6)
  })
})
