import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { DecisionPacket } from '@/lib/decision-packet-api'

import { DecisionPacketIntelligence } from './decision-packet-intelligence'

const packet: DecisionPacket = {
  packet_version: '2',
  state_name: 'Lagos',
  state_slug: 'lagos',
  state_code: 'LA',
  geopolitical_zone: 'South West',
  year: 2026,
  coverage_label: 'Partial 2026 series · 2 of 12 months published',
  months_published: 2,
  annual_gross: '220000000000',
  annual_deductions: '44000000000',
  annual_net: '176000000000',
  deduction_burden_pct: 20,
  net_retention_pct: 80,
  momentum: 'Strengthening',
  momentum_pct: 20,
  volatility: 'Moderate',
  volatility_cv_pct: 10,
  evidence_status: 'Verified',
  igr_records: [],
  igr_note: 'No IGR evidence available.',
  watch_events: [],
  months: [
    {
      revenue_month: '2026-01-01',
      reporting_label: 'January 2026',
      gross_total: '100000000000',
      total_deductions: '20000000000',
      net_allocation: '80000000000',
      reconciliation_status: 'reconciled',
      proof_id: 'GF1-NG-LA-202601-A',
      proof_path: '/fiscal-proof/lagos/2026-01-01',
      source_organization: 'OAGF',
      source_sha256: 'a'.repeat(64),
      human_verified: true,
    },
    {
      revenue_month: '2026-02-01',
      reporting_label: 'February 2026',
      gross_total: '120000000000',
      total_deductions: '24000000000',
      net_allocation: '96000000000',
      reconciliation_status: 'reconciled',
      proof_id: 'GF1-NG-LA-202602-B',
      proof_path: '/fiscal-proof/lagos/2026-02-01',
      source_organization: 'OAGF',
      source_sha256: 'b'.repeat(64),
      human_verified: true,
    },
  ],
  disclaimer: 'Evidence dossier only.',
}

describe('DecisionPacketIntelligence', () => {
  it('renders source-linked analytics and supported workflow actions', () => {
    render(<DecisionPacketIntelligence packet={packet} />)

    expect(
      screen.getByRole('heading', { name: 'What the governed evidence says now' }),
    ).toBeInTheDocument()
    expect(screen.getByText('Monthly gross vs net allocation')).toBeInTheDocument()
    expect(screen.getByText('Deduction pressure')).toBeInTheDocument()
    expect(screen.getByText('+20.00%')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Monitor jurisdiction' })).toHaveAttribute(
      'href',
      '/watchlist',
    )
    expect(
      screen.getByRole('link', { name: 'Get governed intelligence package' }),
    ).toHaveAttribute('href', '/projects')
    expect(screen.getAllByText('Verify proof →')).toHaveLength(2)
    expect(
      screen.getAllByRole('link', { name: /Jan|Feb/ })[0],
    ).toHaveAttribute('href', '/fiscal-proof/lagos/2026-01-01')
  })
})
