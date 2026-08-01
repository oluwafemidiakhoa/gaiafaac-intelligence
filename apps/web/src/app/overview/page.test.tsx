import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { getPublishedOverview } from '@/lib/published-api'
import { publishedOverview } from '@/test/published-fixtures'

import OverviewPage from './page'

vi.mock('@/lib/published-api', () => ({
  getPublishedOverview: vi.fn(),
}))

describe('OverviewPage', () => {
  it('renders the verified national distribution with real coverage', async () => {
    vi.mocked(getPublishedOverview).mockResolvedValue({
      data: publishedOverview,
      error: null,
    })
    render(await OverviewPage())

    expect(screen.getByText('₦5,400.00')).toBeInTheDocument()
    expect(screen.getByText('37 / 37')).toBeInTheDocument()
    expect(screen.getByText('Abia')).toBeInTheDocument()
    expect(screen.queryByText(/DEMO DATA/i)).not.toBeInTheDocument()
  })

  it('keeps a jurisdiction with no published gross unavailable, never zero', async () => {
    vi.mocked(getPublishedOverview).mockResolvedValue({
      data: publishedOverview,
      error: null,
    })
    render(await OverviewPage())

    // Lagos gross and deductions are null → rendered as Unavailable, not ₦0.00.
    expect(screen.getAllByText('Unavailable').length).toBeGreaterThan(0)
    expect(screen.queryByText('₦0.00')).not.toBeInTheDocument()
  })

  it('fails closed when nothing is published', async () => {
    vi.mocked(getPublishedOverview).mockResolvedValue({
      data: null,
      error: 'No verified month is published yet.',
    })
    render(await OverviewPage())

    expect(
      screen.getByText(/No verified month is published yet/i),
    ).toBeInTheDocument()
    expect(screen.queryByText('Abia')).not.toBeInTheDocument()
  })
})
