import type { Metadata } from 'next'

import { FiscalWatchContractsWorkspace } from '@/components/fiscal-watch-contracts-workspace'
import { PageHeader } from '@/components/page-header'

export const metadata: Metadata = {
  title: 'Fiscal Watch Contracts | Gaia Fiscal Intelligence',
  description:
    'Define governed fiscal monitoring mandates tied to Decision Rooms and Fiscal Receipt baselines.',
}

export default function FiscalWatchContractsPage() {
  return (
    <main className="gaia-shell py-12 lg:py-16">
      <PageHeader
        eyebrow="Decision infrastructure · continuous monitoring"
        title="Fiscal Watch Contracts"
        description="Define which governed fiscal changes should reopen an institutional decision. Every match remains tied to the Decision Room, its evidence boundary, and the organization that declared the monitoring mandate."
      />
      <div className="mt-8">
        <FiscalWatchContractsWorkspace />
      </div>
    </main>
  )
}
