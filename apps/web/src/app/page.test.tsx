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
  it('presents the premium governed-intelligence proposition when data is available', async () => {
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
        name: /Know what changed\. Know what evidence supports it\. Preserve what your institution knew when it made the decision\./i,
      }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('link', { name: /Open Fiscal Terminal/i }),
    ).toHaveAttribute('href', '/terminal')
    expect(
      screen.getByRole('link', { name: /Request Institutional Access/i }),
    ).toHaveAttribute('href', '/pilot')
    expect(
      screen.getByRole('heading', {
        name: /Built for expensive decisions/i,
      }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('heading', {
        name: /From government PDFs to decision infrastructure/i,
      }),
    ).toBeInTheDocument()
    expect(screen.getByText('Evidence Fabric')).toBeVisible()
    expect(screen.getByText('Fiscal Intelligence')).toBeVisible()
    expect(screen.getByText('Decision Rails')).toBeVisible()
    expect(screen.queryByRole('navigation')).not.toBeInTheDocument()
  })

  it('renders governed metrics and institutional surfaces', async () => {
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

    expect(screen.getByText('Published capital signal')).toBeVisible()
    expect(screen.getAllByText('Jurisdiction coverage')).toHaveLength(2)
    expect(screen.getByText('Published periods')).toBeVisible()
    expect(screen.getByText('Banks & lenders')).toBeVisible()
    expect(screen.getByText('Investors & DFIs')).toBeVisible()
    expect(screen.getByText('Auditors & governments')).toBeVisible()
  })

  it('fails closed without inventing fiscal totals', async () => {
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
      screen.getByText(/Research workspace unavailable/i),
    ).toBeInTheDocument()
    expect(
      screen.getByText(/does not synthesize replacement values/i),
    ).toBeInTheDocument()
    expect(screen.queryByText('₦5,400.00')).not.toBeInTheDocument()
    expect(screen.queryByText('₦0.00')).not.toBeInTheDocument()
  })
})
