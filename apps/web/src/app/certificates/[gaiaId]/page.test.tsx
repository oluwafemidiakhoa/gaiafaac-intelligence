import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { getFiscalCertificate } from '@/lib/fiscal-ledger-api'

import FiscalCertificatePage from './page'

vi.mock('@/lib/fiscal-ledger-api', () => ({ getFiscalCertificate: vi.fn() }))

const gaiaId = 'GF-CERT-NG-LA-2026H1-A82F91'
const proofId = 'GF-FAAC-NG-LA-202606-FF3373'

describe('FiscalCertificatePage', () => {
  it('renders the immutable package, evidence gaps, and proof links', async () => {
    vi.mocked(getFiscalCertificate).mockResolvedValue({
      data: {
        data: {
          gaia_id: gaiaId,
          jurisdiction: { country: 'NG', code: 'NG-LA', name: 'Lagos State' },
          fiscal_period: '2026H1',
          fiscal_state_id: 'GFS-NG-LA-20260814-A82F91',
          ledger_status: 'partial',
          evidence_coverage: '0.1429',
          evidence_integrity: { score: '74.57', status: 'calculated' },
          verified_domains: ['faac'],
          partial_domains: [],
          unavailable_domains: ['debt', 'liabilities'],
          proof_gaia_ids: [proofId],
          issued_at: '2026-08-14T12:00:00Z',
        },
        evidence: {
          manifest: {
            manifest_version: 'gaia-fiscal-certificate-manifest-v1',
            schema_version: '1.0.0',
            canonicalization_version: 'gaia-canonical-json-v1',
            hash_algorithm: 'sha256',
            payload_sha256: 'a'.repeat(64),
            payload: {},
          },
          disclaimer: 'This certificate is not a credit rating.',
        },
        meta: { schema_version: '1.0.0', methodology_version: '1.0.0' },
      },
      error: null,
    })

    render(
      await FiscalCertificatePage({
        params: Promise.resolve({ gaiaId }),
      }),
    )

    expect(screen.getByText(gaiaId)).toBeVisible()
    expect(screen.getByText('74.57 / 100')).toBeVisible()
    expect(screen.getByText('14.29%')).toBeVisible()
    expect(screen.getByText('debt, liabilities')).toBeVisible()
    expect(screen.getByRole('link', { name: proofId })).toHaveAttribute(
      'href',
      `/proofs/${proofId}`,
    )
    expect(
      screen.getByText('This certificate is not a credit rating.'),
    ).toBeVisible()
  })
})
