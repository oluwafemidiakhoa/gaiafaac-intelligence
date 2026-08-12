import { createHash } from 'node:crypto'

import type { FiscalDesign } from '@/lib/fiscal-design-api'

const fingerprintVersion = 'gaia-fiscal-design-brief-v1'
const manifestVersion = 'gaia-fiscal-design-evidence-manifest-v1'

function compareText(left: string, right: string) {
  return left.localeCompare(right)
}

export function fiscalDesignBriefPayload(
  design: FiscalDesign,
  researchObjective = '',
) {
  const evidence = [...design.evidence]
    .sort((left, right) =>
      compareText(
        `${left.evidence_domain}\u0000${left.label}\u0000${left.reference_path}`,
        `${right.evidence_domain}\u0000${right.label}\u0000${right.reference_path}`,
      ),
    )
    .map((item) => ({
      evidence_domain: item.evidence_domain,
      label: item.label,
      value: item.value,
      source_organization: item.source_organization,
      source_sha256: item.source_sha256,
      reference_path: item.reference_path,
    }))

  const candidates = [...design.candidates]
    .sort((left, right) => compareText(left.key, right.key))
    .map((candidate) => ({
      key: candidate.key,
      title: candidate.title,
      purpose: candidate.purpose,
      status: candidate.status,
      metrics: [...candidate.metrics]
        .sort((left, right) => compareText(left.label, right.label))
        .map((metric) => ({
          label: metric.label,
          value: metric.value,
          unit: metric.unit,
        })),
      note: candidate.note,
    }))

  return {
    fingerprint_version: fingerprintVersion,
    research_objective: researchObjective.trim() || design.objective,
    design_version: design.design_version,
    state_name: design.state_name,
    state_slug: design.state_slug,
    state_code: design.state_code,
    year: design.year,
    latest_comparable_year: design.latest_comparable_year,
    objective: design.objective,
    coverage_label: design.coverage_label,
    faac_months_published: design.faac_months_published,
    faac_complete_year: design.faac_complete_year,
    annual_igr_available: design.annual_igr_available,
    faac_shock_pct: design.faac_shock_pct,
    igr_shock_pct: design.igr_shock_pct,
    reserve_share_pct: design.reserve_share_pct,
    assumptions: [...design.assumptions].sort(compareText),
    evidence,
    candidates,
    disclaimer: design.disclaimer,
  }
}

export function fiscalDesignBriefFingerprint(
  design: FiscalDesign,
  researchObjective = '',
) {
  const payload = fiscalDesignBriefPayload(design, researchObjective)
  return createHash('sha256').update(JSON.stringify(payload)).digest('hex')
}

export function fiscalDesignEvidenceManifest(
  design: FiscalDesign,
  researchObjective = '',
) {
  const payload = fiscalDesignBriefPayload(design, researchObjective)
  const fingerprint = createHash('sha256')
    .update(JSON.stringify(payload))
    .digest('hex')

  return {
    manifest_version: manifestVersion,
    fingerprint_algorithm: 'sha256',
    fingerprint,
    payload,
  }
}
