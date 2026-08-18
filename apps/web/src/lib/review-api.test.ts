import { describe, expect, it } from 'vitest'

import { pendingReviewSchema } from './review-api'

describe('pendingReviewSchema', () => {
  it('parses a valid pending item', () => {
    const parsed = pendingReviewSchema.parse({
      run_id: 'r1',
      reporting_label: 'OAGF Jan 2024',
      revenue_month: '2024-01-01',
      source_organization: 'OAGF',
      status: 'requires_review',
      covered_states: 36,
      expected_states: 37,
      finding_count: 2,
      blocking_count: 2,
      approved: false,
      approved_by: null,
      created_at: '2026-07-31T00:00:00Z',
    })
    expect(parsed.reporting_label).toBe('OAGF Jan 2024')
    expect(parsed.approved).toBe(false)
  })

  it('rejects an item missing coverage', () => {
    expect(() => pendingReviewSchema.parse({ run_id: 'r1' })).toThrow()
  })
})
