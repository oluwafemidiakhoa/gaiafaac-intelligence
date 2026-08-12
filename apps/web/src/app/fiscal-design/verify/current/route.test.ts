import { beforeEach, describe, expect, it, vi } from 'vitest'

import { fiscalDesignBriefFingerprint } from '@/lib/fiscal-design-brief-integrity'
import type { FiscalDesign } from '@/lib/fiscal-design-api'
import { getFiscalDesign } from '@/lib/fiscal-design-api'

import { POST } from './route'

vi.mock('@/lib/fiscal-design-api', () => ({
  getFiscalDesign: vi.fn(),
}))

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
      source_sha256: 'a'.repeat(64),
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

const objective = 'Assess resilience'
const fingerprint = fiscalDesignBriefFingerprint(design, objective)
const requestBody = {
  fingerprint,
  stateSlug: 'lagos',
  year: 2024,
  faacShock: -25,
  igrShock: -10,
  reserveShare: 20,
  researchObjective: objective,
}

function request(body: unknown) {
  return new Request('http://localhost/fiscal-design/verify/current', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

describe('Fiscal Design current evidence route', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('reports a verified manifest as current when fingerprints still match', async () => {
    vi.mocked(getFiscalDesign).mockResolvedValue({ data: design, error: null })

    const response = await POST(request(requestBody))

    expect(response.status).toBe(200)
    await expect(response.json()).resolves.toMatchObject({
      status: 'current',
      manifest_fingerprint: fingerprint,
      current_fingerprint: fingerprint,
      state_name: 'Lagos',
      year: 2024,
    })
    expect(getFiscalDesign).toHaveBeenCalledWith('lagos', 2024, -25, -10, 20)
  })

  it('reports a manifest as superseded when current governed evidence changed', async () => {
    const changed: FiscalDesign = {
      ...design,
      coverage_label: 'Updated governed coverage',
    }
    vi.mocked(getFiscalDesign).mockResolvedValue({ data: changed, error: null })

    const response = await POST(request(requestBody))
    const body = await response.json()

    expect(response.status).toBe(200)
    expect(body.status).toBe('superseded')
    expect(body.current_fingerprint).not.toBe(fingerprint)
  })

  it('fails closed on invalid comparison requests', async () => {
    const response = await POST(request({ fingerprint: 'not-a-sha' }))

    expect(response.status).toBe(400)
    expect(getFiscalDesign).not.toHaveBeenCalled()
  })
})
