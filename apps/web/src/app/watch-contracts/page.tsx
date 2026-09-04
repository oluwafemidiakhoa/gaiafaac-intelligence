import { cookies } from 'next/headers'
import type { Metadata } from 'next'
import Link from 'next/link'

import { FiscalWatchContractsWorkspace } from '@/components/fiscal-watch-contracts-workspace'
import { PageHeader } from '@/components/page-header'

export const metadata: Metadata = {
  title: 'Fiscal Watch Contracts | Gaia Fiscal Intelligence',
  description:
    'Define governed fiscal monitoring mandates with auditable in-app, email and institutional webhook delivery.',
}

export default async function FiscalWatchContractsPage() {
  const authenticated = (await cookies()).has('gaiafaac_session')

  return (
    <main className="gaia-shell py-12 lg:py-16">
      <PageHeader
        eyebrow="Decision infrastructure · continuous monitoring"
        title="Fiscal Watch Contracts"
        description="Define which governed fiscal changes should reopen an institutional decision, then route the resulting review through auditable in-app, opted-in email and institutional webhook delivery. Every match remains tied to its Decision Room and evidence boundary."
      />
      <div className="mt-8">
        {authenticated ? (
          <FiscalWatchContractsWorkspace />
        ) : (
          <section className="rounded-2xl border border-amber-500/20 bg-amber-500/[0.03] p-6 sm:p-8">
            <p className="font-mono text-[0.65rem] font-semibold tracking-[0.16em] text-amber-700 uppercase">
              Organization monitoring workspace
            </p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight">
              Monitoring tied to a decision, not a dashboard.
            </h2>
            <p className="text-muted-foreground mt-3 max-w-3xl text-sm leading-6">
              Watch Contracts are organization-scoped. Sign in before Gaia
              loads private Decision Rooms, monitoring mandates, operational
              reviews or outbound-delivery history.
            </p>
            <Link
              href="/account/login"
              className="mt-5 inline-flex h-10 items-center rounded-md bg-teal-900 px-4 text-sm font-medium text-white transition hover:bg-teal-800"
            >
              Sign in to Watch Contracts
            </Link>
          </section>
        )}
      </div>
    </main>
  )
}
