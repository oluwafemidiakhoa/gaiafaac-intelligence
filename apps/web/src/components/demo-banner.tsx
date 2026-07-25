import { FlaskConical } from 'lucide-react'

export function DemoBanner({
  note = 'Synthetic demonstration records only. These are not real FAAC figures.',
}: {
  note?: string
}) {
  return (
    <aside
      className="border-amber-300 bg-amber-50 text-amber-950 border-y"
      aria-label="Demo data warning"
    >
      <div className="mx-auto flex max-w-7xl items-start gap-3 px-5 py-3 lg:px-8">
        <FlaskConical className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
        <p className="text-sm leading-5">
          <strong className="font-semibold">
            DEMO DATA — NOT REAL FAAC DATA.
          </strong>{' '}
          {note}
        </p>
      </div>
    </aside>
  )
}
