import Link from 'next/link'

import { Button } from '@/components/ui/button'

interface GaiaWorkflowActionsProps {
  question: string
  year: number
  stateSlugs: string[]
  hasEvidence: boolean
}

export function GaiaWorkflowActions({
  question,
  year,
  stateSlugs,
  hasEvidence,
}: GaiaWorkflowActionsProps) {
  const normalized = question.toLowerCase()
  const isScenario = /(shock|reduction|increase|decrease|scenario|what if|20%|10%)/i.test(
    normalized,
  )
  const primaryState = stateSlugs[0]
  const uniqueStates = [...new Set(stateSlugs)].filter(Boolean)

  return (
    <section className="border-border bg-muted/20 rounded-xl border p-5">
      <p className="text-xs font-semibold tracking-wide uppercase">Continue the workflow</p>
      <p className="text-muted-foreground mt-2 text-sm leading-6">
        Gaia can route this evidence into a deterministic institutional workflow. These actions do not change the evidence or silently create an analyst opinion.
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        {uniqueStates.length >= 2 ? (
          <Button asChild size="sm" variant="outline">
            <Link href={`/compare?states=${encodeURIComponent(uniqueStates.join(','))}`}>
              Open comparison
            </Link>
          </Button>
        ) : null}
        {hasEvidence ? (
          <Button asChild size="sm">
            <Link href="/decision-rooms">Create Decision Room</Link>
          </Button>
        ) : null}
        {primaryState ? (
          <Button asChild size="sm" variant="outline">
            <Link href={`/credit-committee-pack?state=${encodeURIComponent(primaryState)}&year=${year}`}>
              Generate Evidence Pack
            </Link>
          </Button>
        ) : null}
        {hasEvidence ? (
          <Button asChild size="sm" variant="outline">
            <Link href="/watch-contracts">Monitor these jurisdictions</Link>
          </Button>
        ) : null}
        {isScenario && primaryState ? (
          <Button asChild size="sm" variant="outline">
            <Link href={`/fiscal-design?state=${encodeURIComponent(primaryState)}&year=${year}`}>
              Open Fiscal Design scenario
            </Link>
          </Button>
        ) : null}
      </div>
    </section>
  )
}
