import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { getPublishedAnalytics } from '@/lib/analytics-api'
import { getPublishedOverview } from '@/lib/published-api'
import { publishedOverview } from '@/test/published-fixtures'

import Home from './page'

vi.mock('@/lib/analytics-api', () => ({
  getPublishedAnalytics: vi.fn(),
}))
vi.mock('@/lib/published-api', () => ({
  getPublishedOverview: vi.fn(),
}))

describe('Home', () => {
  it('provides a focused research entry point with real jurisdictions', async () => {
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

    render(await Home())

    expect(
      screen.getByRole('heading', {
        name: /Understand public finances\. Verify every number\./i,
      }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('link', { name: /Open research terminal/i }),
    ).toHaveAttribute('href', '/terminal')
    expect(
      screen.getByRole('link', { name: /Request institutional access/i }),
    ).toHaveAttribute('href', '/pilot')
    expect(screen.getByRole('combobox', { name: /Jurisdiction/i })).toHaveAttribute(
      'name',
      'q',
    )
    expect(screen.getByRole('button', { name: /Investigate/i })).toBeVisible()
    expect(
      screen.getByRole('link', { name: /Compare jurisdictions/i }),
    ).toHaveAttribute('href', '/compare')
    expect(
      screen.getByRole('link', { name: /Verify the evidence/i }),
    ).toHaveAttribute('href', '/sources')
    expect(
      screen.getByRole('link', { name: /Prepare a decision report/i }),
    ).toHaveAttribute('href', '/decision-packets')
  })

  it('shows the published coverage and period without inventing totals', async () => {
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

    render(await Home())

    expect(screen.getByText('Published jurisdiction coverage')).toBeVisible()
    expect(screen.getByText('Published periods')).toBeVisible()
    expect(screen.getByText('2')).toBeVisible()
    expect(screen.getByText(/Coverage reflects published evidence/i)).toBeVisible()
    expect(screen.queryByText('₦0.00')).not.toBeInTheDocument()
  })

  it('fails closed when published evidence is unavailable', async () => {
    vi.mocked(getPublishedOverview).mockResolvedValue({
      data: null,
      error: 'No published FAAC data is available yet.',
    })
    vi.mocked(getPublishedAnalytics).mockResolvedValue({
      data: null,
      error: 'Analytics are unavailable.',
    })

    render(await Home())

    expect(
      screen.getByText(/Published jurisdiction data is currently unavailable/i),
    ).toBeInTheDocument()
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument()
    expect(screen.getAllByText('Unavailable')).toHaveLength(2)
    expect(screen.queryByText('₦0.00')).not.toBeInTheDocument()
  })
})
