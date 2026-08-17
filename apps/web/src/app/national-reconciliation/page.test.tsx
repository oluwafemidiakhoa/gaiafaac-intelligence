import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import {
  getLatestNationalDistribution,
  type NationalDistribution,
} from '@/lib/national-distribution-api'

import NationalReconciliationPage from './page'

vi.mock('@/lib/national-distribution-api', async () => {
  const actual = await vi.importActual('@/lib/national-distribution-api')
  return {
    ...actual,
    getLatestNationalDistribution: vi.fn(),
  }
})

const distribution: NationalDistribution = {
  reporting_period_id: 'period-1',
  reporting_label: 'June 2026 governed state allocations',
  revenue_month: '2026-06-01',
  disbursement_month: '2026-06-01',
  allocation_period_month: '2026-05-01',
  published_at: '2026-08-17T05:30:10Z',
  verification_status: 'human_verified',
  reported_unit: 'billion_naira',
  derivation_treatment: 'separate',
  states_scope: 'not_declared',
  canonical_source_status: 'missing',
  covered_jurisdictions: 37,
  expected_jurisdictions: 37,
  source: {
    source_organization:
      'Federal Ministry of Information and National Orientation',
    source_url: 'https://example.test/national',
    original_filename: 'faac-may-2026-national.html',
    sha256: 'a'.repeat(64),
    publication_date: '2026-06-17',
    document_version: '1',
    source_type: 'official_government_press_release',
    source_authority: 'official_secondary',
  },
  net_distributable_amount: {
    value: '2300000000000.00',
    evidence_class: 'observed',
  },
  federal_amount: {
    value: '818680000000.00',
    evidence_class: 'observed',
  },
  states_amount: {
    value: '759141000000.00',
    evidence_class: 'observed',
  },
  local_governments_amount: {
    value: '534277000000.00',
    evidence_class: 'observed',
  },
  derivation_amount: {
    value: '188132000000.00',
    evidence_class: 'observed',
  },
  vat_amount: {
    value: '688785000000.00',
    evidence_class: 'observed',
  },
  statutory_amount: {
    value: '1611000000000.00',
    evidence_class: 'observed',
  },
  component_reconciliation: {
    status: 'reconciled',
    observed_total: '2300000000000.00',
    derived_total: '2300230000000.00',
    variance: '230000000.00',
    tolerance: '500000000.00',
    evidence_class: 'derived',
    basis: 'Official recipient components vs distributable total',
    note: 'Reconciled within source precision.',
  },
  jurisdiction_reconciliation: {
    status: 'unavailable',
    observed_total: '759141000000.00',
    derived_total: null,
    variance: null,
    tolerance: null,
    evidence_class: 'missing',
    basis: 'National states aggregate vs jurisdiction ledger',
    note: 'The source does not establish whether FCT is included.',
  },
}

describe('NationalReconciliationPage', () => {
  it('labels allocation and disbursement months separately', async () => {
    vi.mocked(getLatestNationalDistribution).mockResolvedValue({
      data: distribution,
      error: null,
    })

    render(await NationalReconciliationPage())

    expect(screen.getByText('Revenue / allocation period')).toBeVisible()
    expect(screen.getByText('1 May 2026')).toBeVisible()
    expect(screen.getByText('FAAC disbursement month')).toBeVisible()
    expect(screen.getByText('1 Jun 2026')).toBeVisible()
  })

  it(
    'does not infer an allocation period when the API does not provide one',
    async () => {
      vi.mocked(getLatestNationalDistribution).mockResolvedValue({
        data: {
          ...distribution,
          disbursement_month: undefined,
          allocation_period_month: null,
        },
        error: null,
      })

      render(await NationalReconciliationPage())

      expect(screen.getByText('Revenue / allocation period')).toBeVisible()
      expect(screen.getByText('Unavailable')).toBeVisible()
      expect(screen.getByText('FAAC disbursement month')).toBeVisible()
      expect(screen.getByText('1 Jun 2026')).toBeVisible()
    },
  )
})
