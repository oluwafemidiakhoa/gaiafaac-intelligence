import type { Metadata } from 'next'

import { DecisionReviewWorkspace } from '@/components/decision-review-workspace'
import { PageHeader } from '@/components/page-header'

export const metadata: Metadata = {
  title: 'Decision Review | Gaia Fiscal Intelligence',
  description:
    'Review governed changes that reopened an institutional decision and issue a successor Fiscal Receipt with explicit lineage.',
}

export default async function DecisionReviewPage({
  params,
}: {
  params: Promise<{ roomId: string }>
}) {
  const { roomId } = await params

  return (
    <div className="gaia-shell py-12 lg:py-16">
      <PageHeader
        eyebrow="Decision review · governed change"
        title="See what changed before the institution changes its decision."
        description="Gaia keeps the monitoring trigger, prior Fiscal Receipt and successor evidence boundary linked in one review record. Re-review remains a human act; the Receipt records what evidence and lineage were present when that review occurred."
      />
      <div className="mt-8">
        <DecisionReviewWorkspace roomId={roomId} />
      </div>
    </div>
  )
}
