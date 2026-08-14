import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { getPublishedOverview } from '@/lib/published-api'
import { getFiscalEvents } from '@/lib/fiscal-ledger-api'
import { publishedOverview } from '@/test/published-fixtures'

import Home from './page'

vi.mock('@/lib/published-api', () => ({
  getPublishedOverview: vi.fn(),
}))
vi.mock('@/lib/fiscal-ledger-api', () => ({
  getFiscalEvents: vi.fn(),
}))

describe('Home', () => {
  it('leads with fiscal intelligence and links to verified data', async () => {
    vi.mocked(getPublishedOverview).mockResolvedValue({
      data: publishedOverview,
      error: null,
    })
    vi.mocked(getFiscalEvents).mockResolvedValue({
      data: {
        data: [],
        evidence: { record_count: 0, meaning: 'Lifecycle only.' },
        meta: { schema_version: '1.0.0', methodology_version: '1.0.0' },
      },
      error: null,
    })
    render(await Home())

    expect(
      screen.getByRole('heading', {
        name: /The verifiable fiscal ledger for Nigeria/i,
      }),
    ).toBeInTheDocument()
    // Real total shown; no demo labelling anywhere on the live-first homepage.
    expect(screen.getAllByText('₦5,400.00').length).toBeGreaterThan(0)
    expect(screen.queryByText(/DEMO DATA/i)).not.toBeInTheDocument()
    expect(
      screen.getByRole('link', { name: /Explore jurisdictions/i }),
    ).toHaveAttribute('href', '/states')
    expect(
      screen.getAllByRole('link', {
        name: /Verify a manifest|Verification interface/i,
      })[0],
    ).toHaveAttribute('href', '/fiscal-design/verify')
    expect(screen.getByText('Evidence')).toBeVisible()
    expect(screen.getByText('Verification')).toBeVisible()
    expect(screen.getByText('History')).toBeVisible()
  })

  it('fails closed to an awaiting-publication state, inventing no totals', async () => {
    vi.mocked(getPublishedOverview).mockResolvedValue({
      data: null,
      error: 'No published FAAC data is available yet.',
    })
    vi.mocked(getFiscalEvents).mockResolvedValue({
      data: null,
      error: 'Ledger events unavailable.',
    })
    render(await Home())

    expect(screen.getByText(/Verified data coming online/i)).toBeInTheDocument()
    expect(screen.queryByText('₦5,400.00')).not.toBeInTheDocument()
    expect(screen.queryByText('₦0.00')).not.toBeInTheDocument()
  })
})
