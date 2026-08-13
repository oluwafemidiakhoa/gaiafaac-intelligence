import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { fiscalDesignBriefFingerprint } from '@/lib/fiscal-design-brief-integrity'
import type { FiscalDesign } from '@/lib/fiscal-design-api'
import { getFiscalDesign } from '@/lib/fiscal-design-api'

import FiscalDesignBriefPage from './page'

vi.mock('@/lib/fiscal-design-api', () => ({
  getFiscalDesign: vi.fn(),
}))

const sourceSha = 'a'.repeat(64)
const researchObjective =
  'Assess revenue resilience under a severe FAAC decline.'

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
  assumptions: [
    'FAAC scenario change: -25.00%.',
    'IGR scenario change: -10.00%.',
    'Illustrative IGR buffer share: 20.00%.',
  ],
  evidence: [
    {
      evidence_domain: 'faac',
      label: 'January 2024 net FAAC allocation',
      value: '1000.00',
      source_organization: 'OAGF',
      source_sha256: sourceSha,
      reference_path: '/fiscal-proof/lagos/2024-01-01',
    },
    {
      evidence_domain: 'igr',
      label: '2024 annual IGR',
      value: '500.00',
      source_organization: 'National Bureau of Statistics',
      source_sha256: sourceSha,
      reference_path: '/states/lagos',
    },
  ],
  candidates: [
    {
      key: 'faac_shock',
      title: 'FAAC shock scenario',
      purpose: 'Measure the FAAC shock.',
      status: 'available',
      metrics: [
        {
          label: 'Scenario FAAC',
          value: '750.00',
          unit: 'NGN',
        },
      ],
      note: 'The percentage change is an explicit scenario assumption.',
    },
    {
      key: 'igr_buffer',
      title: 'IGR buffer scenario',
      purpose: 'Explore an IGR buffer.',
      status: 'available',
      metrics: [
        {
          label: 'Illustrative buffer at 20.00%',
          value: '90.00',
          unit: 'NGN',
        },
      ],
      note: 'The buffer share is a user-selected research assumption.',
    },
  ],
  disclaimer: 'Research and planning only.',
}

describe('FiscalDesignBriefPage', () => {
  it('verifies a shareable governed brief from the exact scenario inputs', async () => {
    vi.mocked(getFiscalDesign).mockResolvedValue({ data: design, error: null })
    const fingerprint = fiscalDesignBriefFingerprint(design, researchObjective)

    render(
      await FiscalDesignBriefPage({
        searchParams: Promise.resolve({
          state: 'LAGOS',
          year: '2024',
          faacShock: '-25',
          igrShock: '-10',
          reserveShare: '20',
          objective: researchObjective,
          fingerprint,
        }),
      }),
    )

    expect(getFiscalDesign).toHaveBeenCalledWith('lagos', 2024, -25, -10, 20)
    expect(screen.getByText('Verified fingerprint')).toBeInTheDocument()
    expect(screen.getByText(new RegExp(fingerprint))).toBeInTheDocument()
    expect(screen.getByText(researchObjective)).toBeInTheDocument()
    expect(screen.getByText('Complete 12-month year')).toBeInTheDocument()
    expect(screen.getByText('FAAC shock scenario')).toBeInTheDocument()
    expect(screen.getByText('IGR buffer scenario')).toBeInTheDocument()
    expect(screen.getByText('Governed evidence chain')).toBeInTheDocument()
    expect(screen.getAllByText(new RegExp(sourceSha))).toHaveLength(2)
    expect(screen.getByText('Interpretation boundary')).toBeInTheDocument()
    expect(
      screen.getByRole('link', { name: 'Back to Fiscal Design Lab' }),
    ).toHaveAttribute(
      'href',
      '/fiscal-design?state=lagos&year=2024&faacShock=-25&igrShock=-10&reserveShare=20&objective=Assess+revenue+resilience+under+a+severe+FAAC+decline.',
    )
    expect(
      screen.getByRole('link', { name: 'Download evidence manifest' }),
    ).toHaveAttribute(
      'href',
      `/fiscal-design/brief/manifest?state=lagos&year=2024&faacShock=-25&igrShock=-10&reserveShare=20&fingerprint=${fingerprint}&objective=Assess+revenue+resilience+under+a+severe+FAAC+decline.`,
    )
    expect(
      screen.getByRole('link', { name: 'Verify / compare manifest' }),
    ).toHaveAttribute('href', '/fiscal-design/verify')
  })

  it('keeps a stale fingerprint on the manifest link so the endpoint can fail closed', async () => {
    vi.mocked(getFiscalDesign).mockResolvedValue({ data: design, error: null })
    const staleFingerprint = 'b'.repeat(64)

    render(
      await FiscalDesignBriefPage({
        searchParams: Promise.resolve({
          state: 'lagos',
          year: '2024',
          objective: researchObjective,
          fingerprint: staleFingerprint,
        }),
      }),
    )

    expect(screen.getByText('Fingerprint mismatch')).toBeInTheDocument()
    expect(
      screen.getByRole('link', { name: 'Download evidence manifest' }),
    ).toHaveAttribute(
      'href',
      expect.stringContaining(`fingerprint=${staleFingerprint}`),
    )
  })

  it('fails closed when the governed design response is unavailable', async () => {
    vi.mocked(getFiscalDesign).mockResolvedValue({
      data: null,
      error: 'Fiscal Design Lab is unavailable for this selection.',
    })

    render(
      await FiscalDesignBriefPage({
        searchParams: Promise.resolve({ state: 'lagos', year: '2024' }),
      }),
    )

    expect(
      screen.getByText(/Fiscal Design Lab is unavailable for this selection\./),
    ).toBeInTheDocument()
    expect(screen.queryByText('Scenario results')).not.toBeInTheDocument()
    expect(
      screen.queryByText('Governed evidence chain'),
    ).not.toBeInTheDocument()
  })
})
