import { cookies } from 'next/headers'
import type { Metadata } from 'next'
import Link from 'next/link'

import { DecisionReviewQueue } from '@/components/decision-review-queue'
import { EvidenceRoomsWorkspace } from '@/components/evidence-rooms-workspace'
import { PageHeader } from '@/components/page-header'

export const metadata: Metadata = {
  title: 'Fiscal Decision Rooms | Gaia Fiscal Intelligence',
  description:
    'Persistent institutional workspaces that preserve the governed fiscal evidence boundary behind a decision and generate verifiable Fiscal Receipts.',
}

export default async function DecisionRoomsPage() {
  const authenticated = (await cookies()).has('gaiafaac_session')

  return (
    <div className="gaia-shell py-12 lg:py-16">
      <PageHeader
        eyebrow="Institutional decision infrastructure"
        title="Preserve what your institution knew when it made the decision."
        description="A Gaia Fiscal Decision Room binds the decision question, jurisdictions, evidence boundary, governed source records, review notes and Fiscal Receipts into one durable workspace. Evidence remains evidence; interpretation remains interpretation."
      />
      {authenticated ? (
        <>
          <div className="mt-8">
            <DecisionReviewQueue />
          </div>
          <div className="mt-6">
            <EvidenceRoomsWorkspace />
          </div>
        </>
      ) : (
        <section className="mt-8 rounded-2xl border border-amber-500/20 bg-amber-500/[0.03] p-6 sm:p-8">
          <p className="font-mono text-[0.65rem] font-semibold tracking-[0.16em] text-amber-700 uppercase">
            Institutional review queue
          </p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight">
            Decisions reopened by governed change
          </h2>
          <p className="text-muted-foreground mt-3 max-w-3xl text-sm leading-6">
            Decision Rooms are organization-scoped workspaces. Sign in before
            Gaia loads private rooms, review state, evidence captures or Fiscal
            Receipts.
          </p>
          <Link
            href="/account/login"
            className="mt-5 inline-flex h-10 items-center rounded-md bg-teal-900 px-4 text-sm font-medium text-white transition hover:bg-teal-800"
          >
            Sign in to Decision Rooms
          </Link>
        </section>
      )}
    </div>
  )
}
