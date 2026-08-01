import type { PublishedOverview } from '@/lib/published-api'

/**
 * A realistic published-overview fixture for page tests.
 *
 * Deliberately includes a jurisdiction (Lagos) whose gross and deductions are
 * unpublished (`null`) so tests can assert the fail-closed rule: a missing
 * figure renders as "Unavailable", never as ₦0.00 or an inferred value.
 */
export const publishedOverview: PublishedOverview = {
  period: {
    id: 'period-jan-2024',
    reporting_label: 'OAGF FAAC Disbursement — January 2024',
    revenue_month: '2024-01-01',
    faac_meeting_date: '2024-02-15',
    publication_date: '2024-02-20',
    published_at: '2024-02-21T10:00:00Z',
  },
  source: {
    source_organization: 'OAGF',
    source_url: 'https://oagf.gov.ng/reports/Disbursement-January-2024.pdf',
    original_filename: 'Disbursement-January-2024.pdf',
    sha256: '0'.repeat(64),
    publication_date: '2024-02-20',
  },
  covered_states: 37,
  expected_states: 37,
  total_gross: '6000.00',
  total_deductions: '600.00',
  total_net: '5400.00',
  allocations: [
    {
      state_name: 'Abia',
      state_code: 'AB',
      state_slug: 'abia',
      geopolitical_zone: 'South East',
      gross_total: '1000.00',
      total_deductions: '100.00',
      net_allocation: '900.00',
      reported_unit: 'NGN',
    },
    {
      state_name: 'Lagos',
      state_code: 'LA',
      state_slug: 'lagos',
      geopolitical_zone: 'South West',
      gross_total: null,
      total_deductions: null,
      net_allocation: '4500.00',
      reported_unit: 'NGN',
    },
  ],
}
