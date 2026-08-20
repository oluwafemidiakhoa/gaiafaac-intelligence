import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { publishedOverview } from '@/test/published-fixtures'

import { GaiaTerminalSearch } from './gaia-terminal-search'

describe('GaiaTerminalSearch', () => {
  it('shows governed jurisdictions and command workflows by default', () => {
    render(
      <GaiaTerminalSearch
        jurisdictions={publishedOverview.allocations}
        periodLabel={publishedOverview.period.reporting_label}
      />,
    )

    expect(screen.getByText('Lagos')).toBeVisible()
    expect(screen.getByText('Abia')).toBeVisible()
    expect(screen.getByText('Gaia Analyst')).toBeVisible()
    expect(screen.getByText('National Reconciliation')).toBeVisible()
  })

  it('filters jurisdictions without inventing missing results', () => {
    render(
      <GaiaTerminalSearch
        jurisdictions={publishedOverview.allocations}
        periodLabel={publishedOverview.period.reporting_label}
      />,
    )

    fireEvent.change(screen.getByLabelText('Search Gaia Terminal'), {
      target: { value: 'lagos' },
    })

    expect(screen.getByText('Lagos')).toBeVisible()
    expect(screen.queryByText('Abia')).not.toBeInTheDocument()
  })

  it('finds institutional workflows by intent keywords', () => {
    render(
      <GaiaTerminalSearch
        jurisdictions={publishedOverview.allocations}
        periodLabel={publishedOverview.period.reporting_label}
      />,
    )

    fireEvent.change(screen.getByLabelText('Search Gaia Terminal'), {
      target: { value: 'reconciliation' },
    })

    expect(screen.getByText('National Reconciliation')).toBeVisible()
    expect(screen.queryByText('Gaia Analyst')).not.toBeInTheDocument()
  })

  it('fails closed when nothing governed matches the query', () => {
    render(
      <GaiaTerminalSearch
        jurisdictions={publishedOverview.allocations}
        periodLabel={publishedOverview.period.reporting_label}
      />,
    )

    fireEvent.change(screen.getByLabelText('Search Gaia Terminal'), {
      target: { value: 'imaginary fiscal unicorn' },
    })

    expect(screen.getByText('No governed result found')).toBeVisible()
    expect(
      screen.getByText(/does not invent a jurisdiction, workflow or fiscal value/i),
    ).toBeVisible()
  })
})
