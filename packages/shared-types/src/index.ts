export type VerificationStatus =
  | 'pending'
  | 'automatically_validated'
  | 'requires_review'
  | 'human_verified'
  | 'rejected'
  | 'superseded'

export interface HealthResponse {
  status: 'ok'
  service: 'gaiafaac-api'
  version: string
  environment: string
}

export const DEMO_DATA_LABEL = 'DEMO DATA - NOT REAL FAAC DATA' as const

export interface DemoPeriod {
  id: string
  reporting_label: string
  revenue_month: string
  faac_meeting_date: string | null
  publication_date: string | null
  verification_status: VerificationStatus
  is_published: false
}

export interface DemoAllocation {
  state_name: string
  state_code: string
  state_slug: string
  geopolitical_zone: string
  gross_total: string | null
  total_deductions: string | null
  net_allocation: string | null
  reported_unit: string
  verification_status: VerificationStatus
  source_document_id: string
  is_published: false
}

export interface DemoStateSummary {
  name: string
  code: string
  slug: string
  geopolitical_zone: string
  capital: string
  has_demo_allocation: boolean
  demo_net_allocation: string | null
  verification_status: VerificationStatus | null
}

export interface DemoComponent {
  component_type: string
  component_name: string
  gross_amount: string | null
  deduction_amount: string | null
  net_amount: string | null
  reported_unit: string
}

export interface DemoOverviewResponse {
  data_label: typeof DEMO_DATA_LABEL
  scope_note: string
  period: DemoPeriod
  covered_states: number
  expected_states: number
  sample_gross_total: string | null
  sample_deductions_total: string | null
  sample_net_total: string | null
  allocations: DemoAllocation[]
}

export interface DemoStatesResponse {
  data_label: typeof DEMO_DATA_LABEL
  period: DemoPeriod
  states: DemoStateSummary[]
}

export interface DemoStateDetailResponse {
  data_label: typeof DEMO_DATA_LABEL
  period: DemoPeriod
  state: DemoStateSummary
  allocation: DemoAllocation | null
  components: DemoComponent[]
  unavailable_note: string | null
}

export interface DemoComparisonResponse {
  data_label: typeof DEMO_DATA_LABEL
  scope_note: string
  period: DemoPeriod
  states: DemoStateDetailResponse[]
}

export interface DemoSource {
  id: string
  source_organization: string
  source_url: string | null
  original_filename: string
  sha256: string
  mime_type: string
  publication_date: string | null
  downloaded_at: string | null
  document_version: string
  source_status: string
  is_demo: true
}

export interface DemoSourcesResponse {
  data_label: typeof DEMO_DATA_LABEL
  sources: DemoSource[]
}
