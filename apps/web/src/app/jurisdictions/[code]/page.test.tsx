import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import {
  getFiscalEvents,
  getJurisdictionEvidenceSources,
  getJurisdictionFiscalState,
  getJurisdictionFiscalIntelligence,
} from '@/lib/fiscal-ledger-api'

import JurisdictionFiscalStatePage from './page'

vi.mock('@/lib/fiscal-ledger-api', () => ({
  getFiscalEvents: vi.fn(),
  getJurisdictionEvidenceSources: vi.fn(),
  getJurisdictionFiscalState: vi.fn(),
  getJurisdictionFiscalIntelligence: vi.fn(),
}))

const hash = 'a'.repeat(64)
const proofId = 'GF-FAAC-NG-LA-202606-FF3373'

describe('JurisdictionFiscalStatePage', () => {
  it('renders proof-linked claims and keeps missing domains unavailable', async () => {
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
})
