import type { Metadata } from 'next'

import { PageHeader } from '@/components/page-header'
import { WatchlistWorkspace } from '@/components/watchlist-workspace'
import { getPublishedOverview } from '@/lib/published-api'

export const metadata: Metadata = {
  title: 'My Watchlist',
  description:
    'Follow Nigerian jurisdictions and inspect deterministic, evidence-backed fiscal monitoring signals.',
}
export const dynamic = 'force-dynamic'

export default async function WatchlistPage() {
  const overview = await getPublishedOverview()
  const availableStates = (overview.data?.allocations ?? []).map((state) => ({
    state_name: state.state_name,
    state_code: state.state_code,
    state_slug: state.state_slug,
    geopolitical_zone: state.geopolitical_zone,
  }))

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Gaia Watchlist"
        title="Follow the jurisdictions that matter to you."
        description="Build a personal monitoring list and see only deterministic Fiscal Watch signals for the states you follow. Every alert stays inside GaiaFAAC’s published evidence boundary and links back to its Fiscal Proof."
      />
      <WatchlistWorkspace availableStates={availableStates} />
    </div>
  )
}
