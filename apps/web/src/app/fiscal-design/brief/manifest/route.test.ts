import { describe, expect, it, vi } from 'vitest'

import {
  fiscalDesignBriefFingerprint,
  fiscalDesignEvidenceManifest,
} from '@/lib/fiscal-design-brief-integrity'
import type { FiscalDesign } from '@/lib/fiscal-design-api'
import { getFiscalDesign } from '@/lib/fiscal-design-api'

import { GET } from './route'

vi.mock('@/lib/fiscal-design-api', () => ({
  getFiscalDesign: vi.fn(),
}))

const sourceSha = 'a'.repeat(64)
const researchObjective = 'Assess revenue resilience.'

const design: FiscalDesign = {
  design_version: '0.1',
  state_name: 'Lagos',
  state_slug: 'lagos',
  state_code: 'LA',
  year: 2024,
  latest_comparable_year: 2024,
  objective:
    'Explore hypothetical fiscal-resilience scenarios using governed FAAC and IGR evidence.',
  coverage_label: 'Published 2024 FAAC + annual IGR',
  faac_months_published: 12,
  faac_complete_year: true,
  annual_igr_available: true,
  faac_shock_pct: '-25.00',
  igr_shock_pct: '-10.00',
  reserve_share_pct: '20.00',
  assumptions: ['FAAC scenario change: -25.00%.'],
  evidence: [
    {
      evidence_domain: 'faac',
      label: 'January 2024 net FAAC allocation',
      value: '1000.00',
      source_organization: 'OAGF',
      source_sha256: sourceSha,
      reference_path: '/fiscal-proof/lagos/2024-01-01',
    },
  ],
  candidates: [
    {
      key: 'faac_shock',
      title: 'FAAC shock scenario',
      purpose: 'Measure the FAAC shock.',
      status: 'available',
      metrics: [{ label: 'Scenario FAAC', value: '750.00', unit: 'NGN' }],
      note: 'Explicit scenario assumption.',
    },
  ],
  disclaimer: 'Research and planning only.',
}

describe('Fiscal Design evidence manifest route', () => {
  it('downloads the canonical manifest when the fingerprint verifies', async () => {
    vi.mocked(getFiscalDesign).mockResolvedValue({ data: design, error: null })
    const fingerprint = fiscalDesignBriefFingerprint(design, researchObjective)
    const request = new Request(
      `http://localhost/fiscal-design/brief/manifest?state=LAGOS&year=2024&faacShock=-25&igrShock=-10&reserveShare=20&objective=${encodeURIComponent(researchObjective)}&fingerprint=${fingerprint}`,
    )

    const response = await GET(request)
    const body = await response.json()

    expect(getFiscalDesign).toHaveBeenCalledWith('lagos', 2024, -25, -10, 20)
    expect(response.status).toBe(200)
    expect(response.headers.get('content-type')).toContain('application/json')
    expect(response.headers.get('content-disposition')).toBe(
      'attachment; filename="lagos-2024-fiscal-design-evidence.json"',
    )
    expect(response.headers.get('cache-control')).toBe('no-store')
    expect(body).toEqual(
      fiscalDesignEvidenceManifest(design, researchObjective),
    )
  })

  it('returns conflict instead of exporting changed governed evidence', async () => {
    vi.mocked(getFiscalDesign).mockResolvedValue({ data: design, error: null })
    const staleFingerprint = 'b'.repeat(64)
    const request = new Request(
      `http://localhost/fiscal-design/brief/manifest?state=lagos&year=2024&objective=${encodeURIComponent(researchObjective)}&fingerprint=${staleFingerprint}`,
    )

    const response = await GET(request)
    const body = await response.json()

    expect(response.status).toBe(409)
    expect(body.error).toMatch(/no longer matches/)
    expect(body.expected_fingerprint).toBe(staleFingerprint)
    expect(body.current_fingerprint).toBe(
      fiscalDesignBriefFingerprint(design, researchObjective),
    )
  })

  it('rejects unsigned manifest requests', async () => {
    const response = await GET(
      new Request(
        'http://localhost/fiscal-design/brief/manifest?state=lagos&year=2024',
      ),
    )

    expect(response.status).toBe(400)
    expect(getFiscalDesign).not.toHaveBeenCalled()
  })
})
