import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { getDemoOverview } from '@/lib/demo-api'
import { demoOverview } from '@/test/demo-fixtures'

import OverviewPage from './page'

vi.mock('@/lib/demo-api', () => ({
  getDemoOverview: vi.fn(),
}))

describe('OverviewPage', () => {
  it('labels partial totals and coverage without claiming national completeness', async () => {
    vi.mocked(getDemoOverview).mockResolvedValue({
      data: demoOverview,
      error: null,
    })
    render(await OverviewPage())

    expect(screen.getByText('₦5,400.00')).toBeInTheDocument()
    expect(screen.getByText('3 / 37')).toBeInTheDocument()
    expect(
      screen.getAllByText(/not national FAAC totals/i).length,
    ).toBeGreaterThan(0)
    expect(
      screen.getByText(/DEMO DATA — NOT REAL FAAC DATA/i),
    ).toBeInTheDocument()
  })
})
