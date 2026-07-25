import type {
  DemoOverviewResponse,
  DemoStateDetailResponse,
  DemoStatesResponse,
} from '@gaiafaac/shared-types'

export const demoPeriod = {
  id: 'de000000-0000-4000-8000-000000000001',
  reporting_label: 'DEMO DATA — January 2099 synthetic period',
  revenue_month: '2099-01-01',
  faac_meeting_date: '2099-02-01',
  publication_date: '2099-02-02',
  verification_status: 'pending',
  is_published: false,
} as const

export const demoOverview: DemoOverviewResponse = {
  data_label: 'DEMO DATA - NOT REAL FAAC DATA',
  scope_note:
    'Partial synthetic sample covering 3 of 37 jurisdictions. Totals are demo-sample totals, not national FAAC totals.',
  period: demoPeriod,
  covered_states: 3,
  expected_states: 37,
  sample_gross_total: '6000.00',
  sample_deductions_total: '600.00',
  sample_net_total: '5400.00',
  allocations: [
    {
      state_name: 'Lagos',
      state_code: 'LA',
      state_slug: 'lagos',
      geopolitical_zone: 'South West',
      gross_total: '1000.00',
      total_deductions: '100.00',
      net_allocation: '900.00',
      reported_unit: 'naira',
      verification_status: 'pending',
      source_document_id: 'de000000-0000-4000-8000-000000000002',
      is_published: false,
    },
  ],
}

export const demoStates: DemoStatesResponse = {
  data_label: 'DEMO DATA - NOT REAL FAAC DATA',
  period: demoPeriod,
  states: [
    {
      name: 'Abia',
      code: 'AB',
      slug: 'abia',
      geopolitical_zone: 'South East',
      capital: 'Umuahia',
      has_demo_allocation: false,
      demo_net_allocation: null,
      verification_status: null,
    },
    {
      name: 'Lagos',
      code: 'LA',
      slug: 'lagos',
      geopolitical_zone: 'South West',
      capital: 'Ikeja',
      has_demo_allocation: true,
      demo_net_allocation: '900.00',
      verification_status: 'pending',
    },
  ],
}

export const unavailableState: DemoStateDetailResponse = {
  data_label: 'DEMO DATA - NOT REAL FAAC DATA',
  period: demoPeriod,
  state: demoStates.states[0],
  allocation: null,
  components: [],
  unavailable_note: 'No labelled demo allocation is available for this state.',
}
