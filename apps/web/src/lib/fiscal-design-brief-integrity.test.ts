import { describe, expect, it } from 'vitest'

import type { FiscalDesign } from '@/lib/fiscal-design-api'

import { fiscalDesignBriefFingerprint } from './fiscal-design-brief-integrity'

const sourceSha = 'a'.repeat(64)

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
  assumptions: ['Assumption B', 'Assumption A'],
  evidence: [
    {
      evidence_domain: 'igr',
      label: '2024 annual IGR',
      value: '500.00',
      source_organization: 'National Bureau of Statistics',
      source_sha256: sourceSha,
      reference_path: '/states/lagos',
    },
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
      key: 'igr_buffer',
      title: 'IGR buffer scenario',
      purpose: 'Explore an IGR buffer.',
      status: 'available',
      metrics: [
        { label: 'Metric B', value: '90.00', unit: 'NGN' },
        { label: 'Metric A', value: '500.00', unit: 'NGN' },
      ],
      note: 'Research assumption.',
    },
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

describe('fiscalDesignBriefFingerprint', () => {
  it('is stable across semantic collection ordering', () => {
    const reordered: FiscalDesign = {
      ...design,
      assumptions: [...design.assumptions].reverse(),
      evidence: [...design.evidence].reverse(),
      candidates: [...design.candidates]
        .reverse()
        .map((candidate) => ({
          ...candidate,
          metrics: [...candidate.metrics].reverse(),
        })),
    }

    expect(fiscalDesignBriefFingerprint(design, 'Assess resilience')).toBe(
      fiscalDesignBriefFingerprint(reordered, 'Assess resilience'),
    )
  })

  it('changes when governed evidence or the research objective changes', () => {
    const changedEvidence: FiscalDesign = {
      ...design,
      evidence: design.evidence.map((item, index) =>
        index === 0 ? { ...item, source_sha256: 'b'.repeat(64) } : item,
      ),
    }

    const baseline = fiscalDesignBriefFingerprint(design, 'Assess resilience')

    expect(fiscalDesignBriefFingerprint(changedEvidence, 'Assess resilience')).not.toBe(
      baseline,
    )
    expect(fiscalDesignBriefFingerprint(design, 'Assess a different objective')).not.toBe(
      baseline,
    )
  })
})
