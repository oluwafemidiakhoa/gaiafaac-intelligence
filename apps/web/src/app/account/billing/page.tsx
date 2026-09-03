'use client'

import {
  ArrowLeft,
  CheckCircle2,
  CreditCard,
  ReceiptText,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import Link from 'next/link'
import { useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

interface PaymentItem {
  reference: string | null
  amount_naira: string
  status: string
  invoice_number: string | null
  completed_at: string | null
}

interface BillingHistory {
  plan_code: string
  subscription_status: string | null
  current_period_end: string | null
  payments: PaymentItem[]
}

interface VerificationResult {
  status: string
  plan_code: string
  reference: string
  amount_naira: string
  invoice_number: string | null
  current_period_end: string | null
}

async function errorMessage(response: Response) {
  const body = (await response.json().catch(() => ({}))) as {
    detail?: string
    error?: string
  }
  return body.detail ?? body.error ?? 'Request failed.'
}

function naira(value: string) {
  const amount = Number(value)
  if (!Number.isFinite(amount)) return `₦${value}`
  return new Intl.NumberFormat('en-NG', {
    style: 'currency',
    currency: 'NGN',
    maximumFractionDigits: 2,
  }).format(amount)
}

function date(value: string | null) {
  if (!value) return 'Not available'
  return new Intl.DateTimeFormat('en-NG', {
    dateStyle: 'medium',
  }).format(new Date(value))
}

export default function BillingPage() {
  const [billing, setBilling] = useState<BillingHistory | null>(null)
  const [verification, setVerification] = useState<VerificationResult | null>(
    null,
  )
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [renewing, setRenewing] = useState(false)

  async function loadHistory() {
    const response = await fetch('/api/customer/billing/history', {
      cache: 'no-store',
    })
    if (response.status === 401) {
      window.location.assign('/account/login')
      return
    }
    if (!response.ok) {
      setMessage(await errorMessage(response))
      return
    }
    setBilling((await response.json()) as BillingHistory)
  }

  async function verifyReturnedPayment() {
    const params = new URLSearchParams(window.location.search)
    if (params.get('checkout') !== 'return') return
    const reference = params.get('reference') ?? params.get('trxref')
    if (!reference) {
      setMessage(
        'Paystack returned without a payment reference. Your access has not been changed.',
      )
      return
    }

    const response = await fetch(
      `/api/customer/billing/paystack-verify?reference=${encodeURIComponent(reference)}`,
      { method: 'POST' },
    )
    if (!response.ok) {
      setMessage(await errorMessage(response))
      return
    }
    setVerification((await response.json()) as VerificationResult)
    window.history.replaceState({}, '', '/account/billing')
  }

  useEffect(() => {
    void (async () => {
      await verifyReturnedPayment()
      await loadHistory()
      setLoading(false)
    })()
  }, [])

  async function renew() {
    setRenewing(true)
    setMessage('')
    const response = await fetch('/api/customer/billing/renew', {
      method: 'POST',
    })
    if (!response.ok) {
      setMessage(await errorMessage(response))
      setRenewing(false)
      return
    }
    const body = (await response.json()) as { url: string }
    window.location.assign(body.url)
  }

  if (loading) {
    return (
      <div className="gaia-shell gaia-section">
        <div className="gaia-panel flex min-h-48 items-center justify-center p-8">
          <div className="text-center">
            <div className="mx-auto size-8 animate-pulse rounded-full border border-primary/20 bg-primary/10" />
            <p className="text-muted-foreground mt-4 text-sm">
              Verifying billing state…
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="pb-8">
      <section className="border-b border-white/8 bg-[#041915] text-white">
        <div className="gaia-shell py-12 lg:py-16">
          <Link
            href="/account"
            className="inline-flex items-center gap-2 text-sm font-medium text-white/55 transition hover:text-white"
          >
            <ArrowLeft className="size-4" />
            Back to account
          </Link>

          <div className="mt-8 grid gap-8 lg:grid-cols-[1fr_auto] lg:items-end">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-300/15 bg-emerald-300/[0.07] px-3 py-1.5">
                <CreditCard className="size-3.5 text-emerald-300" />
                <span className="font-mono text-[0.65rem] font-bold tracking-[0.18em] text-emerald-100 uppercase">
                  Account / Billing Control Plane
                </span>
              </div>
              <h1 className="mt-5 text-4xl font-semibold tracking-[-0.05em] sm:text-5xl">
                Billing, access and verified payment history.
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-emerald-50/60">
                Paystack-confirmed payments, entitlement activation, renewal
                dates and receipts stay tied to your organization.
              </p>
            </div>
            <Button asChild variant="outline" className="border-white/15 bg-white/[0.04] text-white hover:bg-white/[0.08] hover:text-white">
              <Link href="/pricing">Compare plans</Link>
            </Button>
          </div>
        </div>
      </section>

      <div className="gaia-shell gaia-section">
        {verification ? (
          <div className="mb-8 overflow-hidden rounded-2xl border border-emerald-500/25 bg-emerald-500/[0.08] p-5">
            <div className="flex items-start gap-3">
              <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-emerald-500/10">
                <CheckCircle2 className="size-5 text-emerald-600 dark:text-emerald-300" />
              </div>
              <div>
                <p className="font-semibold">Payment confirmed. Access is active.</p>
                <p className="text-muted-foreground mt-1 text-sm leading-6">
                  {verification.plan_code.toUpperCase()} ·{' '}
                  {naira(verification.amount_naira)} · Receipt{' '}
                  {verification.invoice_number ?? verification.reference}
                </p>
              </div>
            </div>
          </div>
        ) : null}

        {message ? (
          <p className="border-border bg-muted/40 mb-6 rounded-2xl border p-4 text-sm">
            {message}
          </p>
        ) : null}

        <div className="grid gap-5 md:grid-cols-3">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardDescription className="gaia-data-label">Current plan</CardDescription>
                <Sparkles className="text-primary/55 size-4" />
              </div>
              <CardTitle className="pt-3 text-3xl capitalize">
                {billing?.plan_code ?? 'Free'}
              </CardTitle>
            </CardHeader>
            <CardContent className="text-muted-foreground text-sm">
              Status: {billing?.subscription_status ?? 'No paid subscription'}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardDescription className="gaia-data-label">Access through</CardDescription>
                <ShieldCheck className="text-primary/55 size-4" />
              </div>
              <CardTitle className="pt-3 text-2xl">
                {date(billing?.current_period_end ?? null)}
              </CardTitle>
            </CardHeader>
            <CardContent className="text-muted-foreground text-sm">
              Paid access expires unless renewed.
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardDescription className="gaia-data-label">Verified payments</CardDescription>
                <ReceiptText className="text-primary/55 size-4" />
              </div>
              <CardTitle className="pt-3 text-3xl">
                {billing?.payments.length ?? 0}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {billing?.subscription_status ? (
                <Button onClick={renew} disabled={renewing} className="w-full">
                  <CreditCard className="size-4" />
                  {renewing ? 'Opening Paystack…' : 'Renew 30 days'}
                </Button>
              ) : (
                <Button asChild className="w-full">
                  <Link href="/pricing">Choose a paid plan</Link>
                </Button>
              )}
            </CardContent>
          </Card>
        </div>

        <Card className="mt-6 overflow-hidden">
          <CardHeader className="border-border/70 border-b bg-muted/20">
            <div className="flex items-center gap-3">
              <div className="bg-primary/10 flex size-11 items-center justify-center rounded-2xl">
                <ReceiptText className="text-primary size-5" />
              </div>
              <div>
                <CardTitle>Verified payment ledger</CardTitle>
                <CardDescription>
                  Paystack-confirmed transactions recorded by Gaia and tied to this organization.
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-2">
            {!billing?.payments.length ? (
              <div className="py-8 text-center">
                <ReceiptText className="text-muted-foreground/40 mx-auto size-7" />
                <p className="text-muted-foreground mt-3 text-sm">
                  No verified payments have been recorded for this organization yet.
                </p>
              </div>
            ) : (
              <div className="divide-border divide-y">
                {billing.payments.map((payment) => (
                  <div
                    key={payment.reference ?? payment.invoice_number}
                    className="grid gap-2 py-5 text-sm sm:grid-cols-[1fr_auto_auto] sm:items-center sm:gap-8"
                  >
                    <div>
                      <p className="font-semibold tracking-tight">
                        {payment.invoice_number ?? 'Gaia payment'}
                      </p>
                      <p className="text-muted-foreground mt-1 font-mono text-xs">
                        {payment.reference ?? 'Reference unavailable'}
                      </p>
                    </div>
                    <div className="sm:text-right">
                      <p className="font-mono font-semibold">
                        {naira(payment.amount_naira)}
                      </p>
                      <p className="text-muted-foreground mt-1 text-xs capitalize">
                        {payment.status}
                      </p>
                    </div>
                    <p className="text-muted-foreground sm:text-right">
                      {date(payment.completed_at)}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
