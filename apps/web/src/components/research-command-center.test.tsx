import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { PublishedAnalytics } from '@/lib/analytics-api'
import { publishedOverview } from '@/test/published-fixtures'

import { ResearchCommandCenter } from './research-command-center'

const onePeriod: PublishedAnalytics = {
  months_published: 1,
  national_trend: [
    {
      revenue_month: '2024-01-01',
      reporting_label: 'January 2024',
      total_net: '5400.00',
      covered_states: 37,
    },
  ],
  latest_period_label: 'January 2024',
  top_states: [],
  biggest_movers: [],
  note: 'Computed from complete published, human-verified records only.',
}

const twoPeriods: PublishedAnalytics = {
  ...onePeriod,
  months_published: 2,
  national_trend: [
    ...onePeriod.national_trend,
    {
      revenue_month: '2024-02-01',
      reporting_label: 'February 2024',
      total_net: '6200.00',
      covered_states: 37,
    },
  ],
  latest_period_label: 'February 2024',
}

describe('ResearchCommandCenter', () => {
  it('shows an outage state when governed analytics cannot be read', () => {
    render(
      <ResearchCommandCenter
        overview={publishedOverview}
        analytics={null}
        analyticsError="Analytics are unavailable."
      />,
    )

    expect(screen.getByText('Trend data unavailable')).toBeVisible()
    expect(
      screen.getByText(/will not substitute placeholder trend values/i),
    ).toBeVisible()
    expect(
      screen.queryByLabelText('Published national allocation trend'),
    ).not.toBeInTheDocument()
  })

  it('does not draw a trend from only one published period', () => {
    render(
      <ResearchCommandCenter overview={publishedOverview} analytics={onePeriod} />,
    )

    expect(screen.getByText('Insufficient published history')).toBeVisible()
    expect(screen.getByText(/One period is currently available/i)).toBeVisible()
  })

  it('renders the trend once at least two governed periods exist', () => {
    render(
      <ResearchCommandCenter overview={publishedOverview} analytics={twoPeriods} />,
    )

    expect(
      screen.getByLabelText('Published national allocation trend'),
    ).toBeVisible()
    expect(
      screen.queryByText('Insufficient published history'),
    ).not.toBeInTheDocument()
    expect(screen.getByText('Jan')).toBeVisible()
    expect(screen.getByText('Feb')).toBeVisible()
  })
})
