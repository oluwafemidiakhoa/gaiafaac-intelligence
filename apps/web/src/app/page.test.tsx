import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { getPublishedAnalytics } from '@/lib/analytics-api'
import { getNationalDistributionHistory } from '@/lib/national-distribution-api'
import { getPublishedOverview } from '@/lib/published-api'
import { publishedOverview } from '@/test/published-fixtures'

import Home from './page'

vi.mock('@/lib/analytics-api', () => ({
  getPublishedAnalytics: vi.fn(),
}))
vi.mock('@/lib/national-distribution-api', () => ({
  getNationalDistributionHistory: vi.fn(),
}))
vi.mock('@/lib/published-api', () => ({
  getPublishedOverview: vi.fn(),
}))

describe('Home', () => {
  it('leads with evidence-grade fiscal intelligence and governed research actions', async () => {
    vi.mocked(getPublishedOverview).mockResolvedValue({
      data: publishedOverview,
      error: null,
    })
    vi.mocked(getPublishedAnalytics).mockResolvedValue({
      data: null,
      error: 'Analytics are unavailable.',
    })
    vi.mocked(getNationalDistributionHistory).mockResolvedValue({
      data: [],
      error: null,
    })

    render(await Home())

    expect(
      screen.getByRole('heading', {
        name: /Nigeria’s fiscal numbers, with the evidence attached/i,
      }),
    ).toBeInTheDocument()
    expect(screen.getAllByText('₦5,400.00').length).toBeGreaterThan(0)
    expect(screen.queryByText(/DEMO DATA/i)).not.toBeInTheDocument()
    expect(
      screen.getAllByRole('link', { name: /Open Gaia Terminal/i })[0],
    ).toHaveAttribute('href', '/terminal')
    expect(
      screen.getByRole('link', { name: /Inspect the evidence/i }),
    ).toHaveAttribute('href', '/sources')
    expect(screen.getByRole('link', { name: /Export data/i })).toHaveAttribute(
      'href',
      '/account#exports',
    )
    expect(
      screen.getAllByRole('link', { name: /Verify a manifest/i })[0],
    ).toHaveAttribute('href', '/fiscal-design/verify')
    expect(screen.getByText('Source-backed')).toBeVisible()
    expect(screen.getByText('Human-reviewed')).toBeVisible()
    expect(screen.getByText('Version-aware')).toBeVisible()
  })

  it('summarizes missing national evidence without rendering repetitive month cards', async () => {
    vi.mocked(getPublishedOverview).mockResolvedValue({
      data: publishedOverview,
      error: null,
    })
    vi.mocked(getPublishedAnalytics).mockResolvedValue({
      data: {
        months_published: 2,
        national_trend: [
          {
            revenue_month: '2026-05-01',
            reporting_label: 'May 2026',
            total_net: '800000000000.00',
            covered_states: 37,
          },
          {
            revenue_month: '2026-06-01',
            reporting_label: 'June 2026',
            total_net: '879000000000.00',
            covered_states: 37,
          },
        ],
        latest_period_label: 'June 2026',
        top_states: [],
        biggest_movers: [],
        note: 'Published records only.',
      },
      error: null,
    })
    vi.mocked(getNationalDistributionHistory).mockResolvedValue({
      data: [],
      error: null,
    })

    render(await Home())

    expect(
      screen.getByText(/No governed national comparison is published/i),
    ).toBeVisible()
    expect(screen.getByText('2 awaiting evidence')).toBeVisible()
    expect(
      screen.queryByText(
        /No governed national communiqué published for this month/i,
      ),
    ).not.toBeInTheDocument()
  })

  it('fails closed to an awaiting-publication state, inventing no totals', async () => {
    vi.mocked(getPublishedOverview).mockResolvedValue({
      data: null,
      error: 'No published FAAC data is available yet.',
    })
    vi.mocked(getPublishedAnalytics).mockResolvedValue({
      data: null,
      error: 'Analytics are unavailable.',
    })
    vi.mocked(getNationalDistributionHistory).mockResolvedValue({
      data: [],
      error: null,
    })

    render(await Home())

    expect(screen.getByText(/Awaiting publication/i)).toBeInTheDocument()
    expect(
      screen.getByRole('heading', { name: /Research workspace unavailable/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByText(/does not synthesize replacement values/i),
    ).toBeInTheDocument()
    expect(screen.queryByText('₦5,400.00')).not.toBeInTheDocument()
    expect(screen.queryByText('₦0.00')).not.toBeInTheDocument()
  })
})
