import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { getFiscalEvents } from '@/lib/fiscal-ledger-api'

import FiscalEventsPage from './page'

vi.mock('@/lib/fiscal-ledger-api', () => ({ getFiscalEvents: vi.fn() }))

describe('FiscalEventsPage', () => {
  it('renders a deterministic event with jurisdiction and evidence links', async () => {
    vi.mocked(getFiscalEvents).mockResolvedValue({
      data: {
        data: [
          {
            event_id: 'GFE-NG-LA-20260816-A82F91',
            jurisdiction: { country: 'NG', code: 'NG-LA', name: 'Lagos State' },
            event_type: 'claim_superseded',
            severity: 'material',
            effective_at: '2026-06-01T00:00:00Z',
            detected_at: '2026-08-16T09:00:00Z',
            evidence_status: 'verified',
            evidence_ids: ['GF-FAAC-NG-LA-202606-FF3373'],
            calculation: { value_change_percent: '5.799658' },
            explanation:
              'A previous fiscal claim was superseded; both versions remain retained.',
            fiscal_state_id: null,
            methodology_version: '1.0.0',
          },
        ],
        evidence: {
          record_count: 1,
          meaning: 'Events do not infer cause or misconduct.',
        },
        meta: { schema_version: '1.0.0', methodology_version: '1.0.0' },
      },
      error: null,
    })

    render(await FiscalEventsPage({ searchParams: Promise.resolve({}) }))

    expect(
      screen.getByText(
        'A previous fiscal claim was superseded; both versions remain retained.',
      ),
    ).toBeVisible()
    expect(screen.getByRole('link', { name: 'NG-LA' })).toHaveAttribute(
      'href',
      '/jurisdictions/NG-LA',
    )
    expect(
      screen.getByText('Events do not infer cause or misconduct.'),
    ).toBeVisible()
  })
})
