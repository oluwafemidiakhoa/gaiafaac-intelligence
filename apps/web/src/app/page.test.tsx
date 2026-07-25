import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import Home from './page'

describe('Home', () => {
  it('identifies every available figure as demo data', () => {
    render(<Home />)

    expect(
      screen.getByRole('heading', {
        name: 'Nigeria’s Public Revenue, Explained',
      }),
    ).toBeInTheDocument()
    expect(
      screen.getByText(/DEMO DATA — NOT REAL FAAC DATA/i),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('link', { name: /Explore the demo overview/i }),
    ).toHaveAttribute('href', '/overview')
  })
})
