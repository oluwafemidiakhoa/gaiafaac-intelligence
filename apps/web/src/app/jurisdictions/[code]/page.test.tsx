import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import {
  getFiscalEvents,
  getJurisdictionEvidenceSources,
  getJurisdictionFiscalState,
  getJurisdictionFiscalIntelligence,
} from '@/lib/fiscal-ledger-api'
import { getPublishedOverview } from '@/lib/published-api'

import JurisdictionFiscalStatePage from './page'

vi.mock('@/lib/fiscal-ledger-api', () => ({
  getFiscalEvents: vi.fn(),
  getJurisdictionEvidenceSources: vi.fn(),
  getJurisdictionFiscalState: vi.fn(),
  getJurisdictionFiscalIntelligence: vi.fn(),
}))

vi.mock('@/lib/published-api', () => ({
  getPublishedOverview: vi.fn(),
}))

const hash = 'a'.repeat(64)
const proofId = 'GF-FAAC-NG-LA-202606-FF3373'

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

describe('JurisdictionFiscalStatePage', () => {
  it('renders proof-linked claims and keeps missing domains unavailable', async () => {
    vi.mocked(getPublishedOverview).mockResolvedValue({
      data: null,
      error: null,
    })
    vi.mocked(getJurisdictionFiscalIntelligence).mockResolvedValue({
      data: null,
      error: 'Unavailable',
    })
    vi.mocked(getJurisdictionFiscalState).mockResolvedValue({
      data: {
        data: {
          fiscal_state_id: 'GFS-NG-LA-20260814-A82F91',
          jurisdiction: { country: 'NG', code: 'NG-LA', name: 'Lagos State' },
          effective_at: '2026-08-14T00:00:00Z',
          fiscal_period: '2026-YTD',
          ledger_status: 'partial',
          evidence_coverage: '0.1429',
          evidence_coverage_status: 'calculated',
          domains: {
            faac: {
              status: 'verified',
              claims: [
                {
                  gaia_id: proofId,
                  metric: 'faac_net_allocation',
                  fiscal_period: '2026-06',
                  value: '60348388366.77',
                  unit: 'naira',
                  currency: 'NGN',
                  status: 'verified',
                },
              ],
            },
            debt: { status: 'unavailable', claims: [] },
          },
          evidence_integrity: { score: '74.57', status: 'calculated' },
          events: [],
          sources: [],
          previous_state_id: null,
          published_at: '2026-08-14T00:00:00Z',
        },
        evidence: {
          manifest: {
            manifest_version: 'gaia-fiscal-state-manifest-v2',
            schema_version: '1.1.0',
            canonicalization_version: 'gaia-canonical-json-v1',
            hash_algorithm: 'sha256',
            payload_sha256: hash,
            payload: {},
          },
          conflicts: [],
        },
        meta: { schema_version: '1.1.0', methodology_version: '1.1.0' },
      },
      error: null,
    })
    vi.mocked(getFiscalEvents).mockResolvedValue({
      data: {
        data: [],
        evidence: { record_count: 0, meaning: 'No causal inference.' },
        meta: { schema_version: '1.0.0', methodology_version: '1.0.0' },
      },
      error: null,
    })
    vi.mocked(getJurisdictionEvidenceSources).mockResolvedValue({
      data: {
        data: [],
        evidence: {},
        meta: { schema_version: '1.1.0', methodology_version: '1.1.0' },
      },
      error: null,
    })

    render(
      await JurisdictionFiscalStatePage({
        params: Promise.resolve({ code: 'NG-LA' }),
      }),
    )

    expect(screen.getByRole('heading', { name: 'LAGOS STATE' })).toBeVisible()
    expect(screen.getByText('14.29%')).toBeVisible()
    expect(screen.getByText('74.57 / 100')).toBeVisible()
    expect(screen.getByText('₦60,348,388,366.77')).toBeVisible()
    expect(
      screen.getByRole('link', { name: new RegExp(proofId) }),
    ).toHaveAttribute('href', `/proofs/${proofId}`)
    expect(
      screen.getByText(
        'Unavailable. No value has been substituted or inferred.',
      ),
    ).toBeVisible()
  })

  it('guides users to governed state evidence when Fiscal State is unavailable', async () => {
    vi.mocked(getJurisdictionFiscalState).mockResolvedValue({
      data: null,
      error: 'Unavailable',
    })
    vi.mocked(getFiscalEvents).mockResolvedValue({ data: null, error: null })
    vi.mocked(getJurisdictionEvidenceSources).mockResolvedValue({
      data: null,
      error: null,
    })
    vi.mocked(getJurisdictionFiscalIntelligence).mockResolvedValue({
      data: null,
      error: null,
    })
    vi.mocked(getPublishedOverview).mockResolvedValue({
      data: publishedOverview,
      error: null,
    })

    render(
      await JurisdictionFiscalStatePage({
        params: Promise.resolve({ code: 'NG-LA' }),
      }),
    )

    expect(
      screen.getByRole('heading', { name: 'Fiscal State unavailable' }),
    ).toBeVisible()
    expect(
      screen.getByRole('heading', { name: 'Available state evidence' }),
    ).toBeVisible()
    expect(screen.getByText('₦60,348,388,366.77')).toBeVisible()
    expect(
      screen.getByText(/does not substitute for the unpublished Fiscal State/i),
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
