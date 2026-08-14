import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { getFiscalDesign } from '@/lib/fiscal-design-api'

import FiscalDesignPage from './page'

vi.mock('@/lib/fiscal-design-api', () => ({
  getFiscalDesign: vi.fn(),
}))

const sourceSha = 'a'.repeat(64)

describe('FiscalDesignPage', () => {
  it('does not query the service before a state is selected', async () => {
    render(
      await FiscalDesignPage({
        searchParams: Promise.resolve({ year: '2024' }),
      }),
    )

    expect(
      screen.getByText('Start with a governed evidence boundary'),
    ).toBeInTheDocument()
    expect(screen.getByDisplayValue('-20')).toBeInTheDocument()
    expect(screen.getAllByDisplayValue('0')).toHaveLength(6)
    expect(screen.getByDisplayValue('10')).toBeInTheDocument()
    expect(getFiscalDesign).not.toHaveBeenCalled()
  })

  it('renders complete-year scenarios, assumptions, and evidence provenance', async () => {
    vi.mocked(getFiscalDesign).mockResolvedValue({
      data: {
        design_version: 'v0',
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
        faac_shock_pct: '-20.00',
        igr_shock_pct: '0.00',
        reserve_share_pct: '10.00',
        assumptions: [
          'FAAC scenario change: -20.00%.',
          'IGR scenario change: 0.00%.',
          'Illustrative IGR buffer share: 10.00%.',
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
                value: '800.00',
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
                label: 'Illustrative buffer at 10.00%',
                value: '50.00',
                unit: 'NGN',
              },
            ],
            note: 'The buffer share is a user-selected research assumption.',
          },
          {
            key: 'blended_revenue',
            title: 'Blended revenue stress scenario',
            purpose: 'Stress same-year FAAC and IGR.',
            status: 'available',
            metrics: [
              {
                label: 'Scenario envelope',
                value: '1300.00',
                unit: 'NGN',
              },
            ],
            note: 'This is a hypothetical stress scenario.',
          },
        ],
        disclaimer: 'Research and planning only.',
      },
      error: null,
    })

    render(
      await FiscalDesignPage({
        searchParams: Promise.resolve({
          state: 'LAGOS',
          year: '2024',
          faacShock: '-20',
          igrShock: '0',
          reserveShare: '10',
        }),
      }),
    )

    expect(getFiscalDesign).toHaveBeenCalledWith('lagos', 2024, -20, 0, 10)
    expect(screen.getByText('Complete FAAC year')).toBeInTheDocument()
    expect(screen.getByText('Annual IGR available')).toBeInTheDocument()
    expect(screen.getByText('FAAC shock scenario')).toBeInTheDocument()
    expect(screen.getByText('IGR buffer scenario')).toBeInTheDocument()
    expect(
      screen.getByText('Blended revenue stress scenario'),
    ).toBeInTheDocument()
    expect(
      screen.getByText(/FAAC scenario change: -20\.00%\./),
    ).toBeInTheDocument()
    expect(screen.getAllByText(new RegExp(sourceSha))).toHaveLength(2)
    expect(screen.getByText('OAGF')).toBeInTheDocument()
    expect(
      screen.getByText('National Bureau of Statistics'),
    ).toBeInTheDocument()
    expect(screen.getByText('faac')).toBeInTheDocument()
    expect(screen.getByText('igr')).toBeInTheDocument()
    expect(
      screen.getByRole('link', { name: 'Verify evidence manifest' }),
    ).toHaveAttribute('href', '/fiscal-design/verify')
    expect(
      screen.queryByText('Use the latest comparable year'),
    ).not.toBeInTheDocument()
  })

  it('guides incomplete evidence to the latest comparable year without inventing metrics', async () => {
    vi.mocked(getFiscalDesign).mockResolvedValue({
      data: {
        design_version: 'v0',
        state_name: 'Abia',
        state_slug: 'abia',
        state_code: 'AB',
        year: 2026,
        latest_comparable_year: 2025,
        objective:
          'Explore hypothetical fiscal-resilience scenarios using governed FAAC and IGR evidence.',
        coverage_label: 'Published partial-year 2026 FAAC',
        faac_months_published: 5,
        faac_complete_year: false,
        annual_igr_available: false,
        faac_shock_pct: '-20.00',
        igr_shock_pct: '0.00',
        reserve_share_pct: '10.00',
        assumptions: ['No missing periods are inferred or annualized.'],
        evidence: [],
        candidates: [
          {
            key: 'igr_buffer',
            title: 'IGR buffer scenario',
            purpose: 'Explore an IGR buffer.',
            status: 'insufficient_data',
            metrics: [],
            note: 'No published annual IGR record is available for this exact year.',
          },
          {
            key: 'blended_revenue',
            title: 'Blended revenue stress scenario',
            purpose: 'Stress same-year FAAC and IGR.',
            status: 'insufficient_data',
            metrics: [],
            note: 'Missing or partial periods are not annualized or borrowed.',
          },
        ],
        disclaimer: 'Research and planning only.',
      },
      error: null,
    })

    render(
      await FiscalDesignPage({
        searchParams: Promise.resolve({ state: 'abia', year: '2026' }),
      }),
    )

    expect(screen.getByText('Partial FAAC year')).toBeInTheDocument()
    expect(screen.getByText('Annual IGR unavailable')).toBeInTheDocument()
    expect(screen.getAllByText('Insufficient data')).toHaveLength(2)
    expect(
      screen.getByText('Use the latest comparable year'),
    ).toBeInTheDocument()
    const comparableLink = screen.getByRole('link', {
      name: 'Run 2025 comparable year',
    })
    expect(comparableLink).toHaveAttribute(
      'href',
      '/fiscal-design?state=abia&year=2025&faacShock=-20&igrShock=0&reserveShare=10',
    )
    expect(
      screen.getByText(
        'No published annual IGR record is available for this exact year.',
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        'Missing or partial periods are not annualized or borrowed.',
      ),
    ).toBeInTheDocument()
    expect(screen.queryByText('Scenario envelope')).not.toBeInTheDocument()
  })

  it('fails closed when the Fiscal Design service is unavailable', async () => {
    vi.mocked(getFiscalDesign).mockResolvedValue({
      data: null,
      error: 'Fiscal Design Lab is unavailable for this selection.',
    })

    render(
      await FiscalDesignPage({
        searchParams: Promise.resolve({ state: 'lagos', year: '2024' }),
      }),
    )

    expect(
      screen.getByText(/Fiscal Design Lab is unavailable for this selection\./),
    ).toBeInTheDocument()
    expect(screen.queryByText('Evidence chain')).not.toBeInTheDocument()
    expect(screen.queryByText('FAAC shock scenario')).not.toBeInTheDocument()
  })
})
