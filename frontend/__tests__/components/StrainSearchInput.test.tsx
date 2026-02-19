import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { StrainSearchInput } from '@/components/StrainSearchInput'

vi.mock('@/lib/api', () => ({
  autocompleteStrains: vi.fn(),
  analyzeStrain: vi.fn(),
}))

import { autocompleteStrains, analyzeStrain } from '@/lib/api'

const mockAutocomplete = autocompleteStrains as ReturnType<typeof vi.fn>
const mockAnalyzeStrain = analyzeStrain as ReturnType<typeof vi.fn>

describe('StrainSearchInput', () => {
  const mockOnResult = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers({ shouldAdvanceTime: true })
  })

  it('renders search input', () => {
    render(<StrainSearchInput onResult={mockOnResult} />)
    expect(screen.getByPlaceholderText(/Search strains/)).toBeInTheDocument()
  })

  it('shows dropdown with suggestions', async () => {
    mockAutocomplete.mockResolvedValueOnce([
      { name: 'blue dream', category: 'BLUE' },
      { name: 'blue cheese', category: 'PURPLE' },
    ])

    render(<StrainSearchInput onResult={mockOnResult} />)
    const input = screen.getByPlaceholderText(/Search strains/)
    fireEvent.change(input, { target: { value: 'blue' } })

    // Advance past debounce
    vi.advanceTimersByTime(350)

    await waitFor(() => {
      expect(screen.getByText('blue dream')).toBeInTheDocument()
      expect(screen.getByText('blue cheese')).toBeInTheDocument()
    })
  })

  it('calls analyzeStrain on selection', async () => {
    mockAutocomplete.mockResolvedValueOnce([
      { name: 'og kush', category: 'YELLOW' },
    ])
    mockAnalyzeStrain.mockResolvedValueOnce({ category: 'YELLOW', strain_guess: 'og kush' })

    render(<StrainSearchInput onResult={mockOnResult} />)
    const input = screen.getByPlaceholderText(/Search strains/)
    fireEvent.change(input, { target: { value: 'og' } })
    vi.advanceTimersByTime(350)

    await waitFor(() => {
      expect(screen.getByText('og kush')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('og kush'))

    await waitFor(() => {
      expect(mockAnalyzeStrain).toHaveBeenCalledWith('og kush')
      expect(mockOnResult).toHaveBeenCalled()
    })
  })

  it('shows error on analysis failure', async () => {
    mockAutocomplete.mockResolvedValueOnce([
      { name: 'bad strain', category: 'BLUE' },
    ])
    mockAnalyzeStrain.mockRejectedValueOnce(new Error('Not found'))

    render(<StrainSearchInput onResult={mockOnResult} />)
    const input = screen.getByPlaceholderText(/Search strains/)
    fireEvent.change(input, { target: { value: 'bad' } })
    vi.advanceTimersByTime(350)

    await waitFor(() => {
      expect(screen.getByText('bad strain')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('bad strain'))

    await waitFor(() => {
      expect(screen.getByText(/Not found/)).toBeInTheDocument()
    })
  })

  it('does not fetch for short queries', async () => {
    render(<StrainSearchInput onResult={mockOnResult} />)
    const input = screen.getByPlaceholderText(/Search strains/)
    fireEvent.change(input, { target: { value: 'b' } })
    vi.advanceTimersByTime(350)

    await waitFor(() => {
      expect(mockAutocomplete).not.toHaveBeenCalled()
    })
  })

  it('closes dropdown on escape', async () => {
    mockAutocomplete.mockResolvedValueOnce([
      { name: 'gelato', category: 'RED' },
    ])

    render(<StrainSearchInput onResult={mockOnResult} />)
    const input = screen.getByPlaceholderText(/Search strains/)
    fireEvent.change(input, { target: { value: 'gel' } })
    vi.advanceTimersByTime(350)

    await waitFor(() => {
      expect(screen.getByText('gelato')).toBeInTheDocument()
    })

    fireEvent.keyDown(input, { key: 'Escape' })

    await waitFor(() => {
      expect(screen.queryByText('gelato')).not.toBeInTheDocument()
    })
  })
})
