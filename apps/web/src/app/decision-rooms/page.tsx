import type { Metadata } from 'next'

import { DecisionReviewQueue } from '@/components/decision-review-queue'
import { EvidenceRoomsWorkspace } from '@/components/evidence-rooms-workspace'
import { PageHeader } from '@/components/page-header'

export const metadata: Metadata = {
  title: 'Fiscal Decision Rooms | Gaia Fiscal Intelligence',
  description:
    'Persistent institutional workspaces that preserve the governed fiscal evidence boundary behind a decision and generate verifiable Fiscal Receipts.',
}

export default function DecisionRoomsPage() {
  return (
    <div className="gaia-shell py-12 lg:py-16">
      <PageHeader
        eyebrow="Institutional decision infrastructure"
        title="Preserve what your institution knew when it made the decision."
        description="A Gaia Fiscal Decision Room binds the decision question, jurisdictions, evidence boundary, governed source records, review notes and Fiscal Receipts into one durable workspace. Evidence remains evidence; interpretation remains interpretation."
      />
      <div className="mt-8">
        <DecisionReviewQueue />
      </div>
      <div className="mt-6">
        <EvidenceRoomsWorkspace />
      </div>
    </div>
  )
}
