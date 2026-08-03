import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import Dashboard from './Dashboard'
import { getDashboardStats } from '../../services/api'

vi.mock('../../services/api', () => ({
  getDashboardStats: vi.fn(),
  getHealth: vi.fn().mockResolvedValue({ data: { status: 'healthy', model: 'test-model', rag_chunks: 87 } }),
}))

const baseStats = {
  total_leads: 200, hot_leads: 2, warm_leads: 99, cold_leads: 99,
  total_properties: 10, avg_latency_ms: 41.2, requests_this_session: 5,
  lead_conversion_rate: 18.0, avg_lead_score: 49.4,
  revenue_pipeline_aed: 450_400_000, deals_closed_this_month: 7,
}

describe('Dashboard', () => {
  // Regression test: before this fix, an un-evaluated RAGAS score rendered
  // as "0.0000" next to a static "0.97 ✓" target - looked like a passing
  // score instead of missing data.
  it('shows "Not yet evaluated" instead of a fake passing score when RAGAS has not run', async () => {
    vi.mocked(getDashboardStats).mockResolvedValueOnce({
      data: { ...baseStats, ragas_evaluated: false, ragas_faithfulness: null, hallucination_rate: null },
    } as any)
    render(<Dashboard />)

    expect(await screen.findAllByText(/Not yet evaluated/i)).toHaveLength(2) // faithfulness + hallucination cards
    expect(screen.queryByText('0.0000')).not.toBeInTheDocument()
    expect(screen.queryByText(/0\.97 ✓/)).not.toBeInTheDocument()
  })

  it('shows the real faithfulness score once RAGAS has actually been evaluated', async () => {
    vi.mocked(getDashboardStats).mockResolvedValueOnce({
      data: { ...baseStats, ragas_evaluated: true, ragas_faithfulness: 0.913, hallucination_rate: 0.087 },
    } as any)
    render(<Dashboard />)

    expect(await screen.findByText('0.9130')).toBeInTheDocument()
    expect(screen.getByText('0.97 ✓')).toBeInTheDocument()
  })

  it('renders real lead distribution numbers from the API', async () => {
    vi.mocked(getDashboardStats).mockResolvedValueOnce({ data: { ...baseStats, ragas_evaluated: false } } as any)
    render(<Dashboard />)
    expect(await screen.findByText('200')).toBeInTheDocument() // total leads
    expect(screen.getByText('450.4M')).toBeInTheDocument() // pipeline value
  })
})
