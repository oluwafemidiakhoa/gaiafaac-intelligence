import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { getLgaPublicationStatus } from '@/lib/lga-status-api'
import {
  getPublishedLgasForState,
  getPublishedOverview,
} from '@/lib/published-api'

import LocalGovernmentsPage from './page'

vi.mock('@/lib/lga-status-api', () => ({
  getLgaPublicationStatus: vi.fn(),
}))

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
  it('shows the governed LGA pipeline stage while preserving available state evidence', async () => {
    vi.mocked(getPublishedLgasForState).mockResolvedValue({
      data: null,
      error:
        'No published local-government evidence is available for this jurisdiction yet.',
    })
    vi.mocked(getPublishedOverview).mockResolvedValue({
      data: publishedOverview,
      error: null,
    })
    vi.mocked(getLgaPublicationStatus).mockResolvedValue({
      data: {
        state_name: 'Lagos',
        state_code: 'LA',
        stage: 'awaiting_review',
        reporting_label: 'OAGF FAAC Disbursement - June 2026',
        disbursement_month: '2026-06-01',
        source_format: 'excel',
        original_filename: 'Table-IV-June-2026.xlsx',
        source_sha256: hash,
        record_count: 774,
        expected_record_count: 774,
        blocking_count: 0,
        message:
          'The complete extraction is staged for human review before four-eyes publication.',
      },
      error: null,
    })

    render(
      await LocalGovernmentsPage({
        params: Promise.resolve({ code: 'LA' }),
      }),
    )

    expect(
      screen.getByRole('heading', {
        name: 'LGA evidence publication status',
      }),
    ).toBeVisible()
    expect(screen.getByText('Awaiting human review')).toBeVisible()
    expect(screen.getByText('774/774')).toBeVisible()
    expect(screen.getByText('XLSX', { exact: false })).toBeVisible()
    expect(screen.getByText('Table-IV-June-2026.xlsx')).toBeVisible()
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
