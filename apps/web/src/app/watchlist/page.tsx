import type { Metadata } from 'next'

import { NotificationPreferencesCard } from '@/components/notification-preferences-card'
import { OrganizationWatchlistWorkspace } from '@/components/organization-watchlist-workspace'
import { PageHeader } from '@/components/page-header'
import { WatchlistWorkspace } from '@/components/watchlist-workspace'
import { getPublishedOverview } from '@/lib/published-api'

export const metadata: Metadata = {
  title: 'Watchlists',
  description:
    'Follow Nigerian jurisdictions individually or with your organization and inspect deterministic, evidence-backed fiscal monitoring signals.',
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
        eyebrow="Gaia Watchlists"
        title="Monitor what matters — for you and your organization."
        description="Keep an individual jurisdiction list and alert inbox for your own workflow. Team and API organizations can also maintain one shared monitoring perimeter and evidence-backed alert ledger with per-member read receipts. Every alert stays inside GaiaFAAC’s published evidence boundary and links back to its evidence trail."
      />
      <OrganizationWatchlistWorkspace availableStates={availableStates} />

      <div className="mt-12">
        <p className="text-primary font-mono text-xs font-semibold tracking-[0.16em] uppercase">
          Individual monitoring
        </p>
        <h2 className="mt-2 text-2xl font-semibold">Your watchlist</h2>
        <p className="text-muted-foreground mt-2 max-w-3xl text-sm leading-6">
          Your individual watchlist and read state stay separate from the
          organization workspace. Email preferences continue to apply to your
          individual governed alerts and remain subject to GaiaFAAC&apos;s
          delivery controls.
        </p>
      </div>
      <NotificationPreferencesCard />
      <WatchlistWorkspace availableStates={availableStates} />
    </div>
  )
}
