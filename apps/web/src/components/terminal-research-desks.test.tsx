import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { TerminalResearchDesks } from './terminal-research-desks'

describe('TerminalResearchDesks', () => {
  it('links to governed research pages', () => {
    render(<TerminalResearchDesks />)
    const links = [
      ['Explore trends', '/insights'],
      ['Your fiscal watchlist', '/watchlist'],
      ['Audit source registry', '/sources'],
    ]
    for (const [label, href] of links) {
      const link = screen.getByRole('link', { name: label })
      expect(link).toHaveAttribute('href', href)
    }
  })
})
