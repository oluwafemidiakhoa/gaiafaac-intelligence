import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { askGaiaAnalyst } from '@/lib/gaia-analyst-api'

import GaiaAnalystPage from './page'

vi.mock('@/lib/gaia-analyst-api', () => ({
  askGaiaAnalyst: vi.fn(),
}))

describe('GaiaAnalystPage', () => {
  it('surfaces both FAAC and IGR suggested questions before submission', async () => {
    render(
      await GaiaAnalystPage({
        searchParams: Promise.resolve({ year: '2024' }),
      }),
    )

    expect(
      screen.getByText(
        'What changed in the latest published FAAC data for 2024?',
      ),
    ).toBeInTheDocument()
    expect(screen.getByText('What is Lagos IGR in 2024?')).toBeInTheDocument()
    expect(
      screen.getByText('What is the latest published IGR for Lagos?'),
    ).toBeInTheDocument()
    expect(
      screen.getByText('Compare Rivers and Lagos IGR in 2024.'),
    ).toBeInTheDocument()
  })

  it('renders governed IGR provenance in the answer card and evidence record', async () => {
    vi.mocked(askGaiaAnalyst).mockResolvedValue({
      data: {
        question: 'What is Lagos IGR in 2024?',
        year: 2024,
        intent: 'igr_state',
        status: 'answered',
        answer: 'Lagos has a published 2024 annual IGR record of NGN 1,000.00.',
        coverage_label: 'Published 2024 annual IGR · Lagos',
        evidence: [
          {
            state_name: 'Lagos',
            state_slug: 'lagos',
            label: '2024 annual IGR',
            value: 'NGN 1,000.00',
            metric: 'igr_amount',
            reference_path: '/states/lagos',
            reference_label: 'Open state record',
            evidence_domain: 'igr',
            period_label: '2024 annual',
            source_organization: 'National Bureau of Statistics',
            source_sha256: 'a'.repeat(64),
          },
        ],
        caveat: 'Only published, human-verified IGR evidence is used.',
        suggested_questions: ['What is the latest published IGR for Lagos?'],
      },
      error: null,
    })

    render(
      await GaiaAnalystPage({
        searchParams: Promise.resolve({
          question: 'What is Lagos IGR in 2024?',
          year: '2024',
        }),
      }),
    )

    expect(screen.getByText('igr')).toBeInTheDocument()
    expect(screen.getByText('2024 annual')).toBeInTheDocument()
    expect(screen.getByText('Source:')).toBeInTheDocument()
    expect(screen.getAllByText('National Bureau of Statistics')).toHaveLength(2)
    expect(screen.getByText('a'.repeat(64))).toBeInTheDocument()
    expect(screen.getByText('Open state record →')).toBeInTheDocument()
    expect(
      screen.getByText(
        'This IGR answer is restricted to the selected year: 2024.',
      ),
    ).toBeInTheDocument()
    expect(screen.queryByText('Fiscal Proof')).not.toBeInTheDocument()
  })

  it('makes latest-query year semantics explicit', async () => {
    vi.mocked(askGaiaAnalyst).mockResolvedValue({
      data: {
        question: 'What is the latest published IGR for Lagos?',
        year: 2026,
        intent: 'igr_latest',
        status: 'answered',
        answer:
          'The latest published IGR for Lagos is 2024 annual: NGN 1,000.00.',
        coverage_label: 'Latest published IGR · 2024 annual',
        evidence: [
          {
            state_name: 'Lagos',
            state_slug: 'lagos',
            label: '2024 annual IGR',
            value: 'NGN 1,000.00',
            metric: 'igr_amount',
            reference_path: '/states/lagos',
            reference_label: 'Open state record',
            evidence_domain: 'igr',
            period_label: '2024 annual',
            source_organization: 'National Bureau of Statistics',
            source_sha256: 'b'.repeat(64),
          },
        ],
        caveat: 'Only current governed IGR publications are used.',
        suggested_questions: [],
      },
      error: null,
    })

    render(
      await GaiaAnalystPage({
        searchParams: Promise.resolve({
          question: 'What is the latest published IGR for Lagos?',
          year: '2026',
        }),
      }),
    )

    expect(
      screen.getByText(
        'Latest mode is active: the Year field does not restrict this query.',
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        '“Latest” is resolved from the canonical governed IGR publication ledger and is not restricted by the Year field.',
      ),
    ).toBeInTheDocument()
  })

  it('keeps FAAC evidence free of IGR-only provenance fields', async () => {
    vi.mocked(askGaiaAnalyst).mockResolvedValue({
      data: {
        question:
          'Which states received the highest net FAAC allocation in 2024?',
        year: 2024,
        intent: 'top_net',
        status: 'answered',
        answer: 'Lagos ranked first by published net FAAC allocation.',
        coverage_label: 'Published 2024 FAAC',
        evidence: [
          {
            state_name: 'Lagos',
            state_slug: 'lagos',
            label: 'Net allocation',
            value: '₦4,500.00',
            metric: 'net_allocation',
            reference_path: '/fiscal-proof/lagos/2024-01-01',
            reference_label: 'Open Fiscal Proof',
            evidence_domain: 'faac',
            period_label: null,
            source_organization: null,
            source_sha256: null,
          },
        ],
        caveat: 'FAAC answers use published verified ledger evidence.',
        suggested_questions: [
          'What changed in the latest published FAAC data for 2024?',
        ],
      },
      error: null,
    })

    render(
      await GaiaAnalystPage({
        searchParams: Promise.resolve({
          question:
            'Which states received the highest net FAAC allocation in 2024?',
          year: '2024',
        }),
      }),
    )

    expect(screen.getByText('faac')).toBeInTheDocument()
    expect(screen.getByText('Open Fiscal Proof →')).toBeInTheDocument()
    expect(screen.queryByText('Source SHA-256')).not.toBeInTheDocument()
    expect(screen.queryByText('Source:')).not.toBeInTheDocument()
  })

  it('fails closed when Gaia Analyst cannot return published evidence', async () => {
    vi.mocked(askGaiaAnalyst).mockResolvedValue({
      data: null,
      error: 'Gaia Analyst is unavailable.',
    })

    render(
      await GaiaAnalystPage({
        searchParams: Promise.resolve({
          question: 'What is Lagos IGR in 2024?',
          year: '2024',
        }),
      }),
    )

    expect(
      screen.getByText(/Gaia Analyst is unavailable\./),
    ).toBeInTheDocument()
    expect(screen.queryByText('Evidence used')).not.toBeInTheDocument()
  })
})
