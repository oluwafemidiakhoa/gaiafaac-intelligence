import type { Metadata } from 'next'

import { PageHeader } from '@/components/page-header'
import { getPendingReviews } from '@/lib/review-api'

export const metadata: Metadata = { title: 'Pending review' }
export const dynamic = 'force-dynamic'

export default async function PendingReviewPage() {
  const result = await getPendingReviews()
  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Review queue"
        title="Months awaiting review"
        description="Collected from source, imported and validated — not verified and not published until a reviewer approves. Figures are hidden here by design."
      />
      {result.data && result.data.length > 0 ? (
        <div className="mt-8 overflow-x-auto">
          <table className="w-full min-w-3xl border-collapse text-left text-sm">
            <thead>
              <tr className="border-border border-b">
                <th className="py-3 pr-5 font-medium">Report</th>
                <th className="py-3 pr-5 font-medium">Coverage</th>
                <th className="py-3 pr-5 font-medium">Findings</th>
                <th className="py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {result.data.map((item) => (
                <tr
                  key={item.run_id}
                  className="border-border border-b last:border-0"
                >
                  <td className="py-4 pr-5 font-medium">
                    {item.reporting_label}
                  </td>
                  <td className="py-4 pr-5">
                    {item.covered_states} / {item.expected_states}
                  </td>
                  <td className="py-4 pr-5">
                    {item.finding_count} ({item.blocking_count} blocking)
                  </td>
                  <td className="py-4">{item.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="text-muted-foreground mt-10 text-sm">
          Nothing awaiting review. Collected months appear here for approval.
        </p>
      )}
    </div>
  )
}
