import {
  ArrowDown,
  BriefcaseBusiness,
  Building2,
  Database,
  FileCheck2,
  Fingerprint,
  GitCompareArrows,
  Radar,
  Scale,
  ShieldCheck,
} from 'lucide-react'

const decisionChain = [
  { label: 'Official source', icon: FileCheck2 },
  { label: 'Fingerprint', icon: Fingerprint },
  { label: 'Governed evidence', icon: ShieldCheck },
  { label: 'Fiscal signal', icon: Radar },
  { label: 'Decision Room', icon: BriefcaseBusiness },
  { label: 'Fiscal Receipt', icon: Scale },
  { label: 'Monitor what changed', icon: Database },
]

const expensiveDecisions = [
  {
    title: 'Credit underwriting',
    body: 'Assemble traceable fiscal evidence before approving state-linked exposure.',
    icon: Building2,
  },
  {
    title: 'Portfolio surveillance',
    body: 'Watch governed fiscal changes after exposure has been approved.',
    icon: Radar,
  },
  {
    title: 'Investment research',
    body: 'Compare jurisdictions without rebuilding government datasets manually.',
    icon: GitCompareArrows,
  },
  {
    title: 'Due diligence',
    body: 'Freeze an evidence boundary and preserve exactly what was available during review.',
    icon: FileCheck2,
  },
  {
    title: 'Audit & review',
    body: 'Reconstruct what data, calculations and source revisions supported a past decision.',
    icon: ShieldCheck,
  },
  {
    title: 'Data integration',
    body: 'Consume revision-aware governed evidence programmatically.',
    icon: Database,
  },
]

export function CommercialDecisionChain() {
  return (
    <section className="border-b border-slate-200/80 bg-white px-5 py-14 lg:px-8 dark:border-white/10 dark:bg-[#071512]">
      <div className="mx-auto max-w-7xl">
        <div className="flex items-end justify-between gap-6">
          <div>
            <p className="text-xs font-bold tracking-[0.18em] text-emerald-700 uppercase dark:text-emerald-300">
              The decision chain
            </p>
            <h2 className="mt-3 max-w-3xl text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl dark:text-white">
              Evidence becomes durable decision infrastructure only when the
              source trail survives the decision.
            </h2>
          </div>
        </div>

        <ol className="mt-9 grid gap-3 sm:grid-cols-2 lg:grid-cols-7">
          {decisionChain.map(({ label, icon: Icon }, index) => (
            <li
              key={label}
              className="border-slate-200 bg-slate-50/70 relative rounded-xl border p-4 dark:border-white/10 dark:bg-white/[0.035]"
            >
              <div className="flex items-center justify-between gap-3">
                <Icon className="size-4 text-emerald-700 dark:text-emerald-300" />
                <span className="font-mono text-[0.6rem] text-slate-400 dark:text-white/35">
                  {String(index + 1).padStart(2, '0')}
                </span>
              </div>
              <p className="mt-5 text-sm font-semibold text-slate-900 dark:text-white">
                {label}
              </p>
              {index < decisionChain.length - 1 ? (
                <ArrowDown className="mt-3 size-3.5 text-slate-300 lg:hidden dark:text-white/20" />
              ) : null}
            </li>
          ))}
        </ol>
      </div>
    </section>
  )
}

export function ExpensiveDecisionWorkflows() {
  return (
    <section className="bg-[#f7f8f6] px-5 py-20 lg:px-8 lg:py-28 dark:bg-[#06100f]">
      <div className="mx-auto max-w-7xl">
        <div className="max-w-3xl">
          <p className="text-xs font-bold tracking-[0.18em] text-emerald-700 uppercase dark:text-emerald-300">
            Institutional outcomes
          </p>
          <h2 className="mt-4 text-4xl font-semibold tracking-[-0.045em] text-slate-950 sm:text-5xl dark:text-white">
            Built for expensive decisions.
          </h2>
          <p className="mt-5 max-w-2xl text-base leading-7 text-slate-600 dark:text-slate-300/75">
            Gaia is designed to reduce manual research and verification work
            while preserving a defensible evidence boundary before and after
            capital is committed.
          </p>
        </div>

        <div className="mt-10 grid gap-px overflow-hidden rounded-2xl border border-slate-200 bg-slate-200 sm:grid-cols-2 lg:grid-cols-3 dark:border-white/10 dark:bg-white/10">
          {expensiveDecisions.map(({ title, body, icon: Icon }) => (
            <article
              key={title}
              className="bg-white p-6 sm:p-7 dark:bg-[#071512]"
            >
              <Icon className="size-5 text-emerald-700 dark:text-emerald-300" />
              <h3 className="mt-5 text-lg font-semibold text-slate-950 dark:text-white">
                {title}
              </h3>
              <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300/70">
                {body}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
