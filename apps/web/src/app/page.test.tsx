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
  it('displays institutional homepage with fiscal metrics when data is available', async () => {
    vi.mocked(getPublishedOverview).mockResolvedValue({
      data: publishedOverview,
      error: null,
    })
    vi.mocked(getPublishedAnalytics).mockResolvedValue({
      data: {
        months_published: 2,
        national_trend: [],
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
      screen.getByRole('heading', {
        name: /Every fiscal number, traced to source/i,
      }),
    ).toBeInTheDocument()
    expect(
      screen.getAllByRole('link', { name: /Terminal/i })[0],
    ).toHaveAttribute('href', '/terminal')
    expect(
      screen.getAllByRole('link', { name: /Institutions/i })[0],
    ).toHaveAttribute('href', '/institutions')
    expect(
      screen.getByRole('link', { name: /Request Access/i }),
    ).toHaveAttribute('href', '/pricing')
    expect(
      screen.getByRole('heading', {
        name: /Built for institutional confidence/i,
      }),
    ).toBeInTheDocument()
    expect(screen.getByText('Unbroken Chain')).toBeVisible()
    expect(screen.getByText('Four-Eyes Control')).toBeVisible()
  })

  it('displays latest published total and coverage metrics', async () => {
    vi.mocked(getPublishedOverview).mockResolvedValue({
      data: publishedOverview,
      error: null,
    })
    vi.mocked(getPublishedAnalytics).mockResolvedValue({
      data: {
        months_published: 2,
        national_trend: [],
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

    expect(screen.getByText('Latest Published Total')).toBeVisible()
    expect(screen.getByText('Coverage')).toBeVisible()
    expect(screen.getByText('Published Periods')).toBeVisible()
    expect(screen.getByText('All Nigerian states and FCT')).toBeVisible()
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
      screen.getByText(
        /Gaia Fiscal Intelligence does not synthesize replacement values/i,
      ),
    ).toBeInTheDocument()
    expect(screen.queryByText('₦5,400.00')).not.toBeInTheDocument()
    expect(screen.queryByText('₦0.00')).not.toBeInTheDocument()
  })
})
