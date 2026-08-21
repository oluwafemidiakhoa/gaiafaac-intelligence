import type { Metadata } from 'next'

import { EvidenceRoomsWorkspace } from '@/components/evidence-rooms-workspace'
import { PageHeader } from '@/components/page-header'

export const metadata: Metadata = {
  title: 'Evidence Rooms',
  description:
    'Durable organization case files that keep immutable fiscal evidence separate from human notes and decisions.',
}

export default function EvidenceRoomsPage() {
  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Institutional workspace"
        title="Evidence Rooms"
        description="Turn alerts, Fiscal Events, Fiscal Proofs, Decision Packets and retained sources into durable organization case files. Governed evidence is snapshotted and immutable; human commentary remains explicitly separate."
      />
      <div className="mt-8">
        <EvidenceRoomsWorkspace />
      </div>
    </div>
  )
}
