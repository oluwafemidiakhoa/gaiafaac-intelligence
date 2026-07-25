import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { getDemoStates } from '@/lib/demo-api'
import { demoStates } from '@/test/demo-fixtures'

import StatesPage from './page'

vi.mock('@/lib/demo-api', () => ({
  getDemoStates: vi.fn(),
}))

describe('StatesPage', () => {
  it('keeps missing demo allocations unavailable', async () => {
    vi.mocked(getDemoStates).mockResolvedValue({
      data: demoStates,
      error: null,
    })
    render(await StatesPage())

    expect(screen.getByText('Abia')).toBeInTheDocument()
    expect(screen.getAllByText('Unavailable').length).toBeGreaterThan(0)
    expect(screen.getByText('₦900.00')).toBeInTheDocument()
  })
})
