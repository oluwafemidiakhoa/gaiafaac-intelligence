import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { getPublishedOverview } from '@/lib/published-api'
import { publishedOverview } from '@/test/published-fixtures'

import StatesPage from './page'

vi.mock('@/lib/published-api', () => ({
  getPublishedOverview: vi.fn(),
}))

describe('StatesPage', () => {
  it('lists jurisdictions from the verified month with real net allocations', async () => {
    vi.mocked(getPublishedOverview).mockResolvedValue({
      data: publishedOverview,
      error: null,
    })
    render(await StatesPage())

    expect(screen.getByText('Abia')).toBeInTheDocument()
    expect(screen.getByText('₦900.00')).toBeInTheDocument()
    expect(screen.getByText('Lagos')).toBeInTheDocument()
    expect(screen.getByText('₦4,500.00')).toBeInTheDocument()
  })

  it('fails closed when nothing is published', async () => {
    vi.mocked(getPublishedOverview).mockResolvedValue({
      data: null,
      error: 'No verified month is published yet.',
    })
    render(await StatesPage())

    expect(
      screen.getByText(/No verified month is published yet/i),
    ).toBeInTheDocument()
    expect(screen.queryByText('Abia')).not.toBeInTheDocument()
  })
})
