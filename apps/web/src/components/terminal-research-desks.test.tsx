import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { TerminalResearchDesks } from './terminal-research-desks'

describe('TerminalResearchDesks', () => {
  it('links to governed research pages', () => {
    render(<TerminalResearchDesks />)
    expect(screen.getByText('Explore trends')).toHaveAttribute('href', '/insights')
    expect(screen.getByText('Your fiscal watchlist')).toHaveAttribute(
      'href',
      '/watchlist',
    )
    expect(screen.getByText('Audit source registry')).toHaveAttribute(
      'href',
      '/sources',
    )
  })
})
