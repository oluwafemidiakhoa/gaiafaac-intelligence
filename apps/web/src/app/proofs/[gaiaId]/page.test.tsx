import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { getLedgerFiscalProof } from '@/lib/fiscal-ledger-api'

import LedgerFiscalProofPage from './page'

vi.mock('@/lib/fiscal-ledger-api', () => ({
  getLedgerFiscalProof: vi.fn(),
}))

const gaiaId = 'GF-FAAC-NG-LA-202606-A82F91'
const hash = 'a'.repeat(64)
const proof = {
  data: {
    gaia_id: gaiaId,
    object_type: 'faac',
    jurisdiction: {
      country: 'NG' as const,
      code: 'NG-LA',
      name: 'Lagos State',
    },
    fiscal_period: '2026-06',
    metric: 'faac_net_allocation',
    value: '60348388366.77',
    unit: 'naira',
    currency: 'NGN',
    effective_at: '2026-06-01T00:00:00Z',
    methodology_version: '1.0.0',
    supersedes_gaia_id: null,
    superseded_by_gaia_id: null,
    source: {
      publisher: 'OAGF',
      document_url: 'https://example.gov.ng/june-2026.pdf',
      document_sha256: hash,
      publication_date: '2026-07-22',
      page: 5,
      table: 'III',
    },
    verification: {
      status: 'verified' as const,
      source_verified: true,
      reconciled: true,
      human_reviewed: true,
      published: true,
      verified_at: '2026-08-14T10:30:00Z',
      note: 'Integrity and provenance are distinct.',
    },
    published_at: '2026-08-14T10:30:00Z',
  },
  evidence: {
    manifest: {
      manifest_version: 'gaia-fiscal-proof-manifest-v1',
      schema_version: '1.0.0',
      canonicalization_version: 'gaia-canonical-json-v1',
      hash_algorithm: 'sha256' as const,
      payload_sha256: hash,
      payload: {},
    },
    disclaimer: 'This does not prove government data is true.',
    revisions: [],
    conflicts: [],
    history: [
      {
        entry_type: 'human_verified' as const,
        occurred_at: '2026-08-14T10:30:00Z',
        label: 'Human verification recorded.',
        evidence_ids: [gaiaId],
      },
      {
        entry_type: 'published' as const,
        occurred_at: '2026-08-14T10:30:00Z',
        label: 'Immutable Fiscal Proof published.',
        evidence_ids: [gaiaId],
      },
    ],
  },
  meta: { schema_version: '1.0.0' as const, methodology_version: '1.0.0' },
}

describe('LedgerFiscalProofPage', () => {
  it('renders identity, evidence, verification boundaries, and manifest actions', async () => {
    vi.mocked(getLedgerFiscalProof).mockResolvedValue({
      data: proof,
      error: null,
    })

    render(
      await LedgerFiscalProofPage({
        params: Promise.resolve({ gaiaId }),
      }),
    )

    expect(screen.getByText(gaiaId)).toBeVisible()
    expect(screen.getByText('₦60,348,388,366.77')).toBeVisible()
    expect(screen.getByText('Source provenance verified')).toBeVisible()
    expect(
      screen.getByText('Integrity and provenance are distinct.'),
    ).toBeVisible()
    expect(
      screen.getByText('This does not prove government data is true.'),
    ).toBeVisible()
    expect(screen.getByText('Human verification recorded.')).toBeVisible()
    expect(screen.getByText('Immutable Fiscal Proof published.')).toBeVisible()
    expect(
      screen.getByRole('link', { name: 'Download manifest JSON' }),
    ).toHaveAttribute('href', `/proofs/${gaiaId}/manifest`)
    expect(
      screen.getByRole('link', { name: 'Verify in browser' }),
    ).toHaveAttribute('href', '/fiscal-design/verify')
  })
})
