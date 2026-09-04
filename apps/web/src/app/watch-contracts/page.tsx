import type { Metadata } from 'next'

import { FiscalWatchContractsWorkspace } from '@/components/fiscal-watch-contracts-workspace'
import { PageHeader } from '@/components/page-header'

export const metadata: Metadata = {
  title: 'Fiscal Watch Contracts | Gaia Fiscal Intelligence',
  description:
    'Define governed fiscal monitoring mandates with auditable in-app, email and institutional webhook delivery.',
}

export default function FiscalWatchContractsPage() {
  return (
    <main className="gaia-shell py-12 lg:py-16">
      <PageHeader
        eyebrow="Decision infrastructure · continuous monitoring"
        title="Fiscal Watch Contracts"
        description="Define which governed fiscal changes should reopen an institutional decision, then route the resulting review through auditable in-app, opted-in email and institutional webhook delivery. Every match remains tied to its Decision Room and evidence boundary."
      />
      <div className="mt-8">
        <FiscalWatchContractsWorkspace />
      </div>
    </main>
  )
}
