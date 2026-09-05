import type { Metadata } from 'next'
import Link from 'next/link'

import { DataUnavailable } from '@/components/data-unavailable'
import { GaiaWorkflowActions } from '@/components/gaia-workflow-actions'
import { PageHeader } from '@/components/page-header'
import { StatusPill } from '@/components/status-pill'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { askGaiaAnalyst } from '@/lib/gaia-analyst-api'

export const metadata: Metadata = { title: 'Ask Gaia' }
export const dynamic = 'force-dynamic'

const defaultQuestion = 'What is the latest published IGR for Lagos?'

interface GaiaAnalystPageProps {
  searchParams: Promise<{
    question?: string
    year?: string
  }>
}

export default async function GaiaAnalystPage({
  searchParams,
}: GaiaAnalystPageProps) {
  const params = await searchParams
  const currentYear = new Date().getUTCFullYear()
  const parsedYear = Number(params.year ?? currentYear)
  const year = Number.isInteger(parsedYear) ? parsedYear : currentYear
  const question = (params.question ?? '').trim()
  const submitted = question.length >= 3
  const isLatestQuestion = /\blatest\b/i.test(question)
  const result = submitted ? await askGaiaAnalyst(question, year) : null
  const data = result?.data ?? null

  const suggestions = [
    `What changed in the latest published FAAC data for ${year}?`,
    `Which states received the highest net FAAC allocation in ${year}?`,
    `What is Lagos IGR in ${year}?`,
    'What is the latest published IGR for Lagos?',
    `Which states had the highest IGR in ${year}?`,
    `Compare Rivers and Lagos IGR in ${year}.`,
    'How dependent is Lagos on FAAC?',
    'How much debt does Lagos carry relative to revenue?',
  ]

  const workflowStates = data
    ? data.evidence
        .map((item) => item.state_slug)
        .filter((value): value is string => Boolean(value))
    : []
  const igrSources = data
    ? Array.from(
        new Set(
          data.evidence
            .filter((item) => item.evidence_domain === 'igr')
            .map((item) => item.source_organization)
            .filter((value): value is string => Boolean(value)),
        ),
      )
    : []

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <div style={{ fontFamily: 'Georgia, serif' }}>
        <PageHeader
          eyebrow="Ask Gaia"
          title="Evidence-led answers for fiscal decisions"
          description="Ask Gaia answers from verified FAAC, IGR and Fiscal State evidence. It calculates clearly, shows the proof behind each answer, refuses to invent facts, forecasts or ratings, and routes supported answers into the next institutional workflow."
        />
      </div>

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Ask Gaia</CardTitle>
          <CardDescription>
            Ask plain-English questions about allocation changes, rankings,
            state comparisons, IGR, FAAC dependence, debt burden or budget
            execution. Every answer stays tied to available evidence.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form
            method="get"
            className="grid gap-4 lg:grid-cols-[1fr_8rem_auto]"
          >
            <label className="grid gap-2 text-sm font-medium">
              Question
              <input
                name="question"
                defaultValue={question || defaultQuestion}
                minLength={3}
                maxLength={500}
                required
                className="border-input bg-background h-11 rounded-md border px-3 text-sm"
                placeholder="How dependent is Lagos on FAAC?"
              />
            </label>
            <label className="grid gap-2 text-sm font-medium">
              Year
              <input
                name="year"
                type="number"
                min="2000"
                max="2100"
                defaultValue={year}
                className="border-input bg-background h-11 rounded-md border px-3 text-sm"
              />
              <span className="text-muted-foreground text-xs leading-4 font-normal">
                Year-specific questions use this value. “Latest” searches the
                latest governed publication instead.
              </span>
            </label>
            <div className="flex items-end">
              <button
                type="submit"
                className="h-11 w-full rounded-md bg-teal-900 px-5 text-sm font-medium text-white hover:bg-teal-800"
              >
                Ask Gaia
              </button>
            </div>
          </form>
          {submitted && isLatestQuestion ? (
            <p className="text-muted-foreground mt-3 text-xs">
              Latest mode is active: the Year field does not restrict this
              query.
            </p>
          ) : null}
        </CardContent>
      </Card>

      {!submitted ? (
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>Suggested questions</CardTitle>
            <CardDescription>
              Start with a question Gaia can answer directly from governed,
              published evidence—without a paid AI subscription.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2">
            {suggestions.map((suggestion) => (
              <Link
                key={suggestion}
                href={`/gaia-analyst?question=${encodeURIComponent(suggestion)}&year=${year}`}
                className="border-border hover:bg-muted/50 rounded-lg border p-4 text-sm font-medium transition-colors"
              >
                {suggestion}
              </Link>
            ))}
          </CardContent>
        </Card>
      ) : null}

      {submitted && !data ? (
        <div className="mt-8">
          <DataUnavailable
            message={result?.error ?? 'Gaia Analyst is unavailable.'}
          />
        </div>
      ) : null}

      {data ? (
        <div className="mt-8 space-y-6">
          <Card>
            <CardHeader>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <CardTitle>Gaia&apos;s answer</CardTitle>
                  <CardDescription>{data.coverage_label}</CardDescription>
                </div>
                <StatusPill
                  tone={data.status === 'answered' ? 'neutral' : 'demo'}
                >
                  {data.status === 'answered'
                    ? 'Evidence grounded'
                    : data.status}
                </StatusPill>
              </div>
            </CardHeader>
            <CardContent>
              <p className="max-w-4xl text-base leading-7">{data.answer}</p>
              {igrSources.length > 0 ? (
                <p className="text-muted-foreground mt-3 text-sm leading-6">
                  <span className="text-foreground font-medium">Source:</span>{' '}
                  {igrSources.join(', ')}
                </p>
              ) : null}
              {data.intent === 'igr_latest' ? (
                <p className="text-muted-foreground mt-2 text-xs">
                  “Latest” is resolved from the canonical governed IGR
                  publication ledger and is not restricted by the Year field.
                </p>
              ) : data.intent.startsWith('igr_') ? (
                <p className="text-muted-foreground mt-2 text-xs">
                  This IGR answer is restricted to the selected year:{' '}
                  {data.year}.
                </p>
              ) : null}
            </CardContent>
          </Card>

          <GaiaWorkflowActions
            question={question}
            year={data.year}
            stateSlugs={workflowStates}
            hasEvidence={data.evidence.length > 0}
          />

          <Card>
            <CardHeader>
              <CardTitle>Evidence used</CardTitle>
              <CardDescription>
                The exact FAAC, IGR or Fiscal State records used. Open the
                linked state record or Fiscal Proof to inspect the underlying
                published evidence.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {data.evidence.length === 0 ? (
                <p className="text-muted-foreground text-sm">
                  No evidence was returned because this question is unsupported
                  or has insufficient published data.
                </p>
              ) : (
                <div className="space-y-3">
                  {data.evidence.map((item, index) => (
                    <div
                      key={`${item.metric}-${item.state_slug ?? 'ledger'}-${index}`}
                      className="border-border rounded-lg border p-4"
                    >
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="rounded-full bg-teal-100 px-2 py-1 text-xs font-medium tracking-wide text-teal-900 uppercase">
                              {item.evidence_domain}
                            </span>
                            {item.period_label ? (
                              <span className="text-muted-foreground text-xs">
                                {item.period_label}
                              </span>
                            ) : null}
                          </div>
                          <p className="mt-2 font-medium">
                            {item.state_name ? `${item.state_name} · ` : ''}
                            {item.label}
                          </p>
                          <p className="text-muted-foreground mt-1 text-sm leading-6">
                            {item.value}
                          </p>
                        </div>
                        <span className="text-muted-foreground font-mono text-xs">
                          {item.metric}
                        </span>
                      </div>

                      {item.evidence_domain === 'igr' &&
                      (item.source_organization || item.source_sha256) ? (
                        <div className="border-border mt-4 grid gap-2 border-t pt-4 text-xs sm:grid-cols-2">
                          {item.source_organization ? (
                            <div>
                              <p className="text-muted-foreground">Source</p>
                              <p className="mt-1 font-medium">
                                {item.source_organization}
                              </p>
                            </div>
                          ) : null}
                          {item.source_sha256 ? (
                            <div>
                              <p className="text-muted-foreground">
                                Source SHA-256
                              </p>
                              <p
                                className="mt-1 font-mono break-all"
                                title={item.source_sha256}
                              >
                                {item.source_sha256}
                              </p>
                            </div>
                          ) : null}
                        </div>
                      ) : null}

                      {item.gaia_object_id ? (
                        <div className="border-border mt-4 grid gap-2 border-t pt-4 text-xs sm:grid-cols-3">
                          <div>
                            <p className="text-muted-foreground">
                              Gaia object ID
                            </p>
                            <p className="mt-1 font-mono break-all">
                              {item.gaia_object_id}
                            </p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">
                              Evidence status
                            </p>
                            <p className="mt-1 font-medium">
                              {item.evidence_status ?? 'Unavailable'}
                            </p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">
                              Relevant date
                            </p>
                            <p className="mt-1 font-mono">
                              {item.relevant_date ?? 'Unavailable'}
                            </p>
                          </div>
                        </div>
                      ) : null}

                      {item.reference_path && item.reference_label ? (
                        <Link
                          href={item.reference_path}
                          className="mt-3 inline-block text-sm font-medium text-teal-900 hover:underline"
                        >
                          {item.reference_label} →
                        </Link>
                      ) : null}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>What this answer does—and does not—say</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground text-sm leading-6">
                {data.caveat}
              </p>
            </CardContent>
          </Card>

          <div className="grid gap-3 md:grid-cols-2">
            {data.suggested_questions.map((suggestion) => (
              <Link
                key={suggestion}
                href={`/gaia-analyst?question=${encodeURIComponent(suggestion)}&year=${data.year}`}
                className="border-border hover:bg-muted/50 rounded-lg border p-4 text-sm font-medium transition-colors"
              >
                {suggestion}
              </Link>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  )
}
