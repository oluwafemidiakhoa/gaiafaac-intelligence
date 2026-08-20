import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { getPublishedAnalytics } from '@/lib/analytics-api'
import { getLatestNationalDistribution } from '@/lib/national-distribution-api'
import { getPublishedOverview } from '@/lib/published-api'
import { publishedOverview } from '@/test/published-fixtures'

import LivePage from './page'

vi.mock('@/lib/published-api', () => ({
  getPublishedOverview: vi.fn(),
}))

vi.mock('@/lib/analytics-api', () => ({
  getPublishedAnalytics: vi.fn(),
}))

vi.mock('@/lib/national-distribution-api', () => ({
  getLatestNationalDistribution: vi.fn(),
}))

const analytics = {
  months_published: 2,
  national_trend: [
    {
      revenue_month: '2023-12-01',
      reporting_label: 'December 2023',
      total_net: '5000.00',
      covered_states: 37,
    },
    {
      revenue_month: '2024-01-01',
      reporting_label: 'January 2024',
      total_net: '5400.00',
      covered_states: 37,
    },
  ],
  latest_period_label: 'January 2024',
  top_states: [
    {
      state_name: 'Lagos',
      state_slug: 'lagos',
      state_code: 'LA',
      geopolitical_zone: 'South West',
      net_allocation: '4500.00',
    },
  ],
  biggest_movers: [
    {
      state_name: 'Lagos',
      state_slug: 'lagos',
      previous_net: '4000.00',
      current_net: '4500.00',
      change: '500.00',
      pct_change: 12.5,
    },
  ],
  note: 'Computed from published records only.',
}

describe('LivePage', () => {
  it('renders governed movement intelligence without replacing unavailable values', async () => {
    vi.mocked(getPublishedOverview).mockResolvedValue({
      data: publishedOverview,
      error: null,
    })
    vi.mocked(getPublishedAnalytics).mockResolvedValue({
      data: analytics,
      error: null,
    })
    vi.mocked(getLatestNationalDistribution).mockResolvedValue({
      data: null,
      error: null,
    })

    render(await LivePage())

    expect(screen.getByText('Know what changed. Trace exactly why.')).toBeVisible()
    expect(screen.getByText('+8.0% vs prior published period')).toBeVisible()
    expect(screen.getByText('+12.5%')).toBeVisible()
    expect(screen.getAllByText('Unavailable').length).toBeGreaterThan(0)
    expect(screen.queryByText('₦0.00')).not.toBeInTheDocument()
    expect(screen.getByText('Awaiting evidence')).toBeVisible()
  })

  it('fails closed when no governed publication exists', async () => {
    vi.mocked(getPublishedOverview).mockResolvedValue({
      data: null,
      error: 'No verified month is published yet.',
    })
    vi.mocked(getPublishedAnalytics).mockResolvedValue({
      data: null,
      error: 'Analytics are unavailable.',
    })
    vi.mocked(getLatestNationalDistribution).mockResolvedValue({
      data: null,
      error: null,
    })

    render(await LivePage())

    expect(
      screen.getByText('Governed intelligence appears only after publication.'),
    ).toBeVisible()
    expect(screen.getByText(/No verified month is published yet/i)).toBeVisible()
    expect(screen.queryByText('Lagos')).not.toBeInTheDocument()
  })
})
