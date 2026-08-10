import type { Metadata } from 'next'
import Link from 'next/link'

import { DataUnavailable } from '@/components/data-unavailable'
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

export const metadata: Metadata = { title: 'Gaia Analyst' }
export const dynamic = 'force-dynamic'

const defaultQuestion = 'What changed in the latest published FAAC data?'

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
  const result = submitted ? await askGaiaAnalyst(question, year) : null
  const data = result?.data ?? null

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Gaia Analyst"
        title="Ask the verified fiscal ledger"
        description="Natural-language questions over published GaiaFAAC evidence. The analyst calculates from deterministic ledger services and refuses unsupported claims instead of guessing."
      />

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Ask a fiscal question</CardTitle>
          <CardDescription>
            v1 supports latest changes, rankings, deduction burden, volatility,
            momentum and two-state comparisons.
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
                placeholder="Compare Rivers and Lagos in 2026"
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
            </label>
            <div className="flex items-end">
              <button
                type="submit"
                className="bg-primary text-primary-foreground h-11 w-full rounded-md px-5 text-sm font-medium"
              >
                Ask Gaia
              </button>
            </div>
          </form>
        </CardContent>
      </Card>

      {!submitted ? (
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>Suggested questions</CardTitle>
            <CardDescription>
              Start with a question that can be resolved directly from the
              verified ledger.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2">
            {[
              `What changed in the latest published FAAC data for ${year}?`,
              `Which states received the highest net FAAC allocation in ${year}?`,
              `Which states had the highest deduction burden in ${year}?`,
              `Which states were the most volatile in ${year}?`,
              `Which states have weakening momentum in ${year}?`,
              `Compare Rivers and Lagos in ${year}.`,
            ].map((suggestion) => (
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
                  <CardTitle>Analyst answer</CardTitle>
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
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Evidence used</CardTitle>
              <CardDescription>
                Structured ledger outputs supporting the answer. Open the linked
                record or Fiscal Proof to inspect the source evidence.
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
                          <p className="font-medium">
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
                      {item.reference_path && item.reference_label ? (
                        <Link
                          href={item.reference_path}
                          className="text-primary mt-3 inline-block text-sm font-medium hover:underline"
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
              <CardTitle>Evidence boundary</CardTitle>
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
