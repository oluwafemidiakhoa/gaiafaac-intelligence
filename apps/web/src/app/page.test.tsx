import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { getPublishedOverview } from '@/lib/published-api'
import { publishedOverview } from '@/test/published-fixtures'

import Home from './page'

vi.mock('@/lib/published-api', () => ({
  getPublishedOverview: vi.fn(),
}))

describe('Home', () => {
  it('leads with fiscal intelligence and links to verified data', async () => {
    vi.mocked(getPublishedOverview).mockResolvedValue({
      data: publishedOverview,
      error: null,
    })
    render(await Home())

    expect(
      screen.getByRole('heading', {
        name: /Verified fiscal intelligence for every Nigerian state/i,
      }),
    ).toBeInTheDocument()
    // Real total shown; no demo labelling anywhere on the live-first homepage.
    expect(screen.getAllByText('₦5,400.00').length).toBeGreaterThan(0)
    expect(screen.queryByText(/DEMO DATA/i)).not.toBeInTheDocument()
    expect(
      screen.getByRole('link', { name: /Explore Fiscal Pulse/i }),
    ).toHaveAttribute('href', '/fiscal-pulse')
    expect(
      screen.getByRole('link', { name: /View verified data/i }),
    ).toHaveAttribute('href', '/live')
  })

  it('fails closed to an awaiting-publication state, inventing no totals', async () => {
    vi.mocked(getPublishedOverview).mockResolvedValue({
      data: null,
      error: 'No published FAAC data is available yet.',
    })
    render(await Home())

    expect(screen.getByText(/Verified data coming online/i)).toBeInTheDocument()
    expect(screen.queryByText('₦5,400.00')).not.toBeInTheDocument()
    expect(screen.queryByText('₦0.00')).not.toBeInTheDocument()
  })
})
