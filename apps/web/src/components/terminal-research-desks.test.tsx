import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { TerminalResearchDesks } from './terminal-research-desks'

describe('TerminalResearchDesks', () => {
  it('links only to existing evidence-governed research workflows', () => {
    render(<TerminalResearchDesks />)

    const expected = [
      ['Explore trends', '/insights'],
      ['Compare jurisdictions', '/compare'],
      ['Your fiscal watchlist', '/watchlist'],
      ['National reconciliation', '/national-reconciliation'],
    ]
    for (const [label, href] of expected) {
      const card = screen.getByRole('link', { name: new RegExp(label, 'i') })
      expect(card).toHaveAttribute('href', href)
    }
    expect(screen.getByRole('link', { name: /audit source registry/i })).toHaveAttribute('href', '/sources')
  })

  it('does not misrepresent fiscal figures as market quotes', () => {
    render(<TerminalResearchDesks />)
    expect(screen.getByText(/not stock quotes, trades or investment recommendations/i)).toBeVisible()
    expect(screen.getByText(/missing evidence is not treated as zero/i)).toBeVisible()
  })
})
