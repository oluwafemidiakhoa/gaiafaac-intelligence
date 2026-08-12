import { describe, expect, it } from 'vitest'

import { fiscalDesignEvidenceManifest } from '@/lib/fiscal-design-brief-integrity'
import type { FiscalDesign } from '@/lib/fiscal-design-api'

import {
  summarizeFiscalDesignPayloadChanges,
  verifyFiscalDesignEvidenceManifestText,
} from './fiscal-design-manifest-verifier'

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

describe('verifyFiscalDesignEvidenceManifestText', () => {
  it('verifies an unchanged Gaia evidence manifest', async () => {
    const manifest = fiscalDesignEvidenceManifest(design, 'Assess resilience')

    await expect(
      verifyFiscalDesignEvidenceManifestText(JSON.stringify(manifest, null, 2)),
    ).resolves.toEqual({
      status: 'verified',
      fingerprint: manifest.fingerprint,
      stateName: 'Lagos',
      year: 2024,
      evidenceCount: 1,
      payload: manifest.payload,
      currentEvidenceCheck: {
        fingerprint: manifest.fingerprint,
        stateSlug: 'lagos',
        year: 2024,
        faacShock: -25,
        igrShock: -10,
        reserveShare: 20,
        researchObjective: 'Assess resilience',
      },
    })
  })

  it('detects a changed payload', async () => {
    const manifest = fiscalDesignEvidenceManifest(design, 'Assess resilience')
    const changed = {
      ...manifest,
      payload: { ...manifest.payload, coverage_label: 'Changed coverage' },
    }

    const result = await verifyFiscalDesignEvidenceManifestText(
      JSON.stringify(changed),
    )

    expect(result.status).toBe('mismatch')
    if (result.status === 'mismatch') {
      expect(result.computedFingerprint).not.toBe(result.fingerprint)
    }
  })

  it('rejects malformed or unsupported manifests', async () => {
    await expect(
      verifyFiscalDesignEvidenceManifestText('{not-json'),
    ).resolves.toEqual({
      status: 'invalid',
      message: 'The manifest is not valid JSON.',
    })

    await expect(
      verifyFiscalDesignEvidenceManifestText(
        JSON.stringify({ manifest_version: 'unknown' }),
      ),
    ).resolves.toEqual({
      status: 'invalid',
      message: 'Unsupported or missing Gaia evidence manifest version.',
    })
  })
})

describe('summarizeFiscalDesignPayloadChanges', () => {
  it('explains coverage, provenance, assumptions, and scenario changes', () => {
    const previous = fiscalDesignEvidenceManifest(
      design,
      'Assess resilience',
    ).payload
    const current = {
      ...previous,
      coverage_label: 'Updated governed coverage',
      faac_months_published: 11,
      assumptions: ['FAAC scenario change: -30.00%.'],
      evidence: previous.evidence.map((item) => ({
        ...item,
        value: '1100.00',
        source_sha256: 'b'.repeat(64),
      })),
      candidates: previous.candidates.map((candidate) => ({
        ...candidate,
        metrics: candidate.metrics.map((metric) => ({
          ...metric,
          value: '700.00',
        })),
      })),
    }

    expect(summarizeFiscalDesignPayloadChanges(previous, current)).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ category: 'coverage' }),
        expect.objectContaining({
          category: 'evidence',
          detail: expect.stringContaining('source hash, value'),
        }),
        expect.objectContaining({ category: 'assumptions' }),
        expect.objectContaining({ category: 'scenario' }),
      ]),
    )
  })

  it('reports added and removed evidence records without inferring data', () => {
    const previous = fiscalDesignEvidenceManifest(
      design,
      'Assess resilience',
    ).payload
    const replacement = {
      ...previous.evidence[0],
      label: 'February 2024 net FAAC allocation',
      reference_path: '/fiscal-proof/lagos/2024-02-01',
    }
    const current = { ...previous, evidence: [replacement] }

    const changes = summarizeFiscalDesignPayloadChanges(previous, current)

    expect(changes).toEqual(
      expect.arrayContaining([
        {
          category: 'evidence',
          detail: 'Evidence removed: January 2024 net FAAC allocation.',
        },
        {
          category: 'evidence',
          detail: 'Evidence added: February 2024 net FAAC allocation.',
        },
      ]),
    )
  })
})
