import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { AnalyzeForm } from '@/components/AnalyzeForm'

// Mock the API module
vi.mock('@/lib/api', () => ({
  analyzeUrl: vi.fn(),
}))

import { analyzeUrl } from '@/lib/api'

const mockAnalyzeUrl = analyzeUrl as ReturnType<typeof vi.fn>

describe('AnalyzeForm', () => {
  const mockOnResult = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders input and submit button', () => {
    render(<AnalyzeForm onResult={mockOnResult} />)
    expect(screen.getByPlaceholderText(/example\.com/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Analyze/i })).toBeInTheDocument()
  })

  it('disables button when input is empty', () => {
    render(<AnalyzeForm onResult={mockOnResult} />)
    const button = screen.getByRole('button', { name: /Analyze/i })
    expect(button).toBeDisabled()
  })

  it('enables button when URL is entered', () => {
    render(<AnalyzeForm onResult={mockOnResult} />)
    const input = screen.getByPlaceholderText(/example\.com/)
    fireEvent.change(input, { target: { value: 'https://example.com/strain' } })
    const button = screen.getByRole('button', { name: /Analyze/i })
    expect(button).not.toBeDisabled()
  })

  it('shows loading state during submission', async () => {
    mockAnalyzeUrl.mockImplementation(() => new Promise(() => {})) // never resolves
    render(<AnalyzeForm onResult={mockOnResult} />)

    const input = screen.getByPlaceholderText(/example\.com/)
    fireEvent.change(input, { target: { value: 'https://example.com/strain' } })
    fireEvent.submit(input.closest('form')!)

    await waitFor(() => {
      expect(screen.getByText(/Analyzing/)).toBeInTheDocument()
    })
  })

  it('calls onResult with data on success', async () => {
    const mockResult = { category: 'BLUE', strain_guess: 'Test' }
    mockAnalyzeUrl.mockResolvedValueOnce(mockResult)

    render(<AnalyzeForm onResult={mockOnResult} />)
    const input = screen.getByPlaceholderText(/example\.com/)
    fireEvent.change(input, { target: { value: 'https://example.com/strain' } })
    fireEvent.submit(input.closest('form')!)

    await waitFor(() => {
      expect(mockOnResult).toHaveBeenCalledWith(mockResult)
    })
  })

  it('shows error message on failure', async () => {
    mockAnalyzeUrl.mockRejectedValueOnce(new Error('Network error'))

    render(<AnalyzeForm onResult={mockOnResult} />)
    const input = screen.getByPlaceholderText(/example\.com/)
    fireEvent.change(input, { target: { value: 'https://example.com/strain' } })
    fireEvent.submit(input.closest('form')!)

    await waitFor(() => {
      expect(screen.getByText(/Network error/)).toBeInTheDocument()
    })
  })

  it('renders help text below the form', () => {
    render(<AnalyzeForm onResult={mockOnResult} />)
    expect(screen.getByText(/Paste a URL/)).toBeInTheDocument()
  })
})
