import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import {
  getPublishedLgasForState,
  getPublishedOverview,
} from '@/lib/published-api'

import LocalGovernmentsPage from './page'

vi.mock('@/lib/published-api', () => ({
  getPublishedLgasForState: vi.fn(),
  getPublishedOverview: vi.fn(),
}))

const hash = 'a'.repeat(64)

const publishedOverview = {
  period: {
    id: 'period-2026-06',
    reporting_label: 'OAGF FAAC Disbursement - June 2026',
    revenue_month: '2026-06-01',
    faac_meeting_date: null,
    publication_date: null,
    published_at: null,
  },
  source: {
    source_organization: 'OAGF',
    source_url: null,
    original_filename: 'Disbursement-June-2026.pdf',
    sha256: hash,
    publication_date: null,
  },
  covered_states: 37,
  expected_states: 37,
  total_gross: null,
  total_deductions: null,
  total_net: '879000000000.00',
  allocations: [
    {
      state_name: 'Lagos',
      state_code: 'LA',
      state_slug: 'lagos',
      geopolitical_zone: 'South West',
      gross_total: '78573057073.75',
      total_deductions: '18224668706.98',
      net_allocation: '60348388366.77',
      reported_unit: 'naira',
    },
  ],
}

describe('LocalGovernmentsPage', () => {
  it('guides users to state evidence without substituting for missing LGA evidence', async () => {
    vi.mocked(getPublishedLgasForState).mockResolvedValue({
      data: null,
      error:
        'No published local-government evidence is available for this jurisdiction yet.',
    })
    vi.mocked(getPublishedOverview).mockResolvedValue({
      data: publishedOverview,
      error: null,
    })

    render(
      await LocalGovernmentsPage({
        params: Promise.resolve({ code: 'LA' }),
      }),
    )

    expect(
      screen.getByRole('heading', {
        name: 'Published LGA evidence unavailable',
      }),
    ).toBeVisible()
    expect(
      screen.getByRole('heading', { name: 'Available state evidence' }),
    ).toBeVisible()
    expect(screen.getByText('₦60,348,388,366.77')).toBeVisible()
    expect(
      screen.getByText(/does not substitute for missing LGA evidence/i),
    ).toBeVisible()
    expect(
      screen.getByRole('link', { name: 'Open state evidence' }),
    ).toHaveAttribute('href', '/states/lagos')
    expect(
      screen.getByRole('link', { name: 'Verify allocation' }),
    ).toHaveAttribute('href', '/fiscal-proof/lagos/2026-06-01')
    expect(
      screen.getByRole('link', { name: 'Decision Packet' }),
    ).toHaveAttribute('href', '/decision-packets/lagos?year=2026')
  })
})
