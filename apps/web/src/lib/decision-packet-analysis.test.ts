import { describe, expect, it } from 'vitest'

import {
  analyzeFiscalEvidence,
  fromKobo,
  percentage,
  proofHref,
  toKobo,
  type FiscalMonth,
} from './decision-packet-analysis'

function month(index: number, net = '80.00'): FiscalMonth {
  const period = `2026-${String(index).padStart(2, '0')}-01`
  return {
    revenue_month: period,
    gross_total: fromKobo(toKobo(net)! + BigInt(2000)),
    total_deductions: '20.00',
    net_allocation: net,
    proof_id: `test-${index}`,
    proof_path: `/fiscal-proof/lagos/${period}`,
    source_organization: 'Synthetic fixture',
    source_sha256: 'a'.repeat(64),
    human_verified: true,
    reconciliation_status: 'reconciled',
  }
}

describe('fiscal evidence arithmetic', () => {
  it.each([null, undefined, '', ' ', 'NaN', 'Infinity', '1e3', '0x10', '1.001', true])(
    'does not coerce missing or malformed money %s to zero',
    (value) => expect(toKobo(value)).toBeNull(),
  )
  it('preserves zero, signed adjustments, and amounts beyond safe float precision', () => {
    expect(toKobo('0.00')).toBe(BigInt(0))
    expect(toKobo('-0.01')).toBe(BigInt(-1))
    expect(fromKobo(toKobo('9007199254740993.01')!)).toBe('9007199254740993.01')
  })
  it('guards zero denominators and rounds only the displayed percentage', () => {
    expect(percentage(BigInt(1), BigInt(0))).toBeNull()
    expect(percentage(BigInt(1), BigInt(3))).toBe(33.33)
    expect(percentage(BigInt(-1), BigInt(3))).toBe(-33.33)
  })
  it('sorts observations without modifying the input', () => {
    const input = [month(3), month(1), month(2)]
    const result = analyzeFiscalEvidence(input, 2026)
    expect(result.rows[0].month.revenue_month).toBe('2026-01-01')
    expect(input[0].revenue_month).toBe('2026-03-01')
  })
  it('shows different, valid endpoint and recent-flow comparisons', () => {
    const input = ['100', '200', '100', '90', '110', '130'].map((n, i) => month(i + 1, n))
    const result = analyzeFiscalEvidence(input, 2026)
    expect(result.firstToLatest).toBe(30)
    expect(result.momentum).toBe(-17.5)
    expect(result.prior.map((row) => row.month.revenue_month)).toEqual([
      '2026-01-01', '2026-02-01', '2026-03-01',
    ])
    expect(result.recent[0].month.revenue_month).toBe('2026-04-01')
  })
  it('does not imply a comparative trend from one observation', () => {
    const result = analyzeFiscalEvidence([month(1)], 2026)
    expect(result.firstToLatest).toBeNull()
    expect(result.momentum).toBeNull()
  })
  it('preserves missing fields and calendar gaps', () => {
    const incomplete = { ...month(3), net_allocation: null }
    const result = analyzeFiscalEvidence([month(1), incomplete], 2026)
    expect(result.slots[1].row).toBeNull()
    expect(result.rows[1].net).toBeNull()
    expect(result.totals.net).toBeNull()
    expect(result.checkedCount).toBe(1)
  })
  it('detects a one-kobo arithmetic discrepancy without repairing it', () => {
    const input = { ...month(1), net_allocation: '79.99' }
    const result = analyzeFiscalEvidence([input], 2026)
    expect(result.residuals[0].residual).toBe(BigInt(1))
    expect(input.net_allocation).toBe('79.99')
  })
  it('refuses derived comparisons over duplicate periods', () => {
    const result = analyzeFiscalEvidence([month(1), month(1, '90'), month(2)], 2026)
    expect(result.structurallyValid).toBe(false)
    expect(result.slots[0].conflict).toBe(true)
    expect(result.firstToLatest).toBeNull()
    expect(result.totals.net).toBeNull()
  })
  it('reports out-of-year and invalid periods rather than mixing years', () => {
    const input = [month(1), { ...month(2), revenue_month: '2025-02-01' }]
    const result = analyzeFiscalEvidence(input, 2026)
    expect(result.invalidPeriodCount).toBe(1)
    expect(result.totals.net).toBeNull()
  })
  it('counts valid source digests once regardless of letter case', () => {
    const input = [month(1), { ...month(2), source_sha256: 'A'.repeat(64) }]
    expect(analyzeFiscalEvidence(input, 2026).sourceCount).toBe(1)
    input[1].source_sha256 = 'not-a-digest'
    expect(analyzeFiscalEvidence(input, 2026).sourceCount).toBe(1)
  })
  it('handles a complete twelve-month window', () => {
    const result = analyzeFiscalEvidence(Array.from({ length: 12 }, (_, i) => month(i + 1)), 2026)
    expect(result.rows).toHaveLength(12)
    expect(result.slots.filter((slot) => slot.row)).toHaveLength(12)
    expect(result.totals.net).toBe(BigInt(96000))
  })
  it('does not navigate a supplied external or protocol-relative proof URL', () => {
    expect(proofHref(month(1))).toBe('/fiscal-proof/lagos/2026-01-01')
    expect(proofHref({ ...month(1), proof_path: '//example.com' })).toBeNull()
    expect(proofHref({ ...month(1), proof_path: 'https://example.com' })).toBeNull()
  })
})
