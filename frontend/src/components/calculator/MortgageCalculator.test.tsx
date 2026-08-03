import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import MortgageCalculator from './MortgageCalculator'
import api from '../../services/api'

vi.mock('../../services/api', () => ({
  default: { post: vi.fn() },
  getHealth: vi.fn().mockResolvedValue({ data: { status: 'healthy', model: 'test-model', rag_chunks: 87 } }),
}))
vi.mock('react-hot-toast', () => ({ default: { error: vi.fn(), success: vi.fn() } }))

const mockResult = {
  monthly_payment_aed: 8234, interest_rate_pct: 4.5, tenure_years: 25,
  down_payment_aed: 500000, down_payment_pct: 25, loan_amount_aed: 1500000,
  total_repayment_aed: 2470200, total_interest_aed: 970200,
  debt_burden_ratio_pct: 27.4, total_cash_needed_aed: 620000,
  closing_costs: { dld_transfer_fee_aed: 80000, agent_commission_aed: 40000, total_closing_costs_aed: 120000 },
  recommended_banks: ['Emirates NBD — from 3.99% fixed'],
}

describe('MortgageCalculator', () => {
  beforeEach(() => { vi.mocked(api.post).mockReset() })

  it('shows the empty state before any calculation', () => {
    render(<MortgageCalculator />)
    expect(screen.getByText(/Fill in the details/i)).toBeInTheDocument()
  })

  it('calls the mortgage API with the form values and renders the result', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ data: mockResult })
    render(<MortgageCalculator />)

    fireEvent.click(screen.getByRole('button', { name: /Calculate Mortgage/i }))

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/tools/mortgage', expect.objectContaining({
      property_price_aed: 2000000, down_payment_pct: 25, interest_rate_pct: 4.5,
    })))
    expect(await screen.findByText(/AED 8,234/)).toBeInTheDocument()
    expect(screen.getByText(/You qualify/i)).toBeInTheDocument()
  })

  it('flags a DBR over the 50% UAE Central Bank limit instead of showing it as passing', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ data: { ...mockResult, debt_burden_ratio_pct: 61.2 } })
    render(<MortgageCalculator />)
    fireEvent.click(screen.getByRole('button', { name: /Calculate Mortgage/i }))
    expect(await screen.findByText(/Exceeds limit/i)).toBeInTheDocument()
  })

  it('shows an error toast and no result when the API call fails', async () => {
    const toast = (await import('react-hot-toast')).default
    vi.mocked(api.post).mockRejectedValueOnce(new Error('network error'))
    render(<MortgageCalculator />)
    fireEvent.click(screen.getByRole('button', { name: /Calculate Mortgage/i }))
    await waitFor(() => expect(toast.error).toHaveBeenCalledWith('Calculation failed'))
    expect(screen.getByText(/Fill in the details/i)).toBeInTheDocument()
  })
})
