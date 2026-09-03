'use client'

import { ArrowLeft, CheckCircle2, CreditCard, ReceiptText } from 'lucide-react'
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
    // Billing hydration verifies a Paystack return before loading entitlement state.
    // eslint-disable-next-line react-hooks/set-state-in-effect
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
      <div className="mx-auto max-w-6xl px-5 py-16 text-sm">
        Verifying billing state…
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-6xl px-5 py-12 lg:px-8 lg:py-16">
      <Link
        href="/account"
        className="text-muted-foreground inline-flex items-center gap-2 text-sm font-medium hover:text-foreground"
      >
        <ArrowLeft className="size-4" />
        Back to account
      </Link>

      <div className="mt-8 flex flex-wrap items-end justify-between gap-5">
        <div>
          <p className="text-primary font-mono text-xs font-semibold tracking-[0.18em] uppercase">
            Revenue engine
          </p>
          <h1 className="mt-3 text-4xl font-semibold tracking-tight">
            Billing & access
          </h1>
          <p className="text-muted-foreground mt-3 max-w-2xl leading-7">
            Payments, entitlement activation, renewal dates and receipts are tied
            to your organization and verified against Paystack.
          </p>
        </div>
        <Button asChild variant="outline">
          <Link href="/pricing">Compare plans</Link>
        </Button>
      </div>

      {verification ? (
        <div className="mt-8 rounded-2xl border border-emerald-500/25 bg-emerald-500/10 p-5">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-emerald-600 dark:text-emerald-300" />
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
        <p className="border-border bg-muted/30 mt-6 rounded-md border p-4 text-sm">
          {message}
        </p>
      ) : null}

      <div className="mt-8 grid gap-5 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardDescription>Current plan</CardDescription>
            <CardTitle className="text-3xl capitalize">
              {billing?.plan_code ?? 'Free'}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-muted-foreground text-sm">
            Status: {billing?.subscription_status ?? 'No paid subscription'}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardDescription>Access through</CardDescription>
            <CardTitle className="text-2xl">
              {date(billing?.current_period_end ?? null)}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-muted-foreground text-sm">
            Paid access expires unless renewed.
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardDescription>Verified payments</CardDescription>
            <CardTitle className="text-3xl">
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

      <Card className="mt-6">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="bg-primary/10 flex size-10 items-center justify-center rounded-xl">
              <ReceiptText className="text-primary size-5" />
            </div>
            <div>
              <CardTitle>Payment receipts</CardTitle>
              <CardDescription>
                Paystack-confirmed transactions recorded by Gaia.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {!billing?.payments.length ? (
            <p className="text-muted-foreground text-sm">
              No verified payments have been recorded for this organization yet.
            </p>
          ) : (
            <div className="divide-border divide-y">
              {billing.payments.map((payment) => (
                <div
                  key={payment.reference ?? payment.invoice_number}
                  className="grid gap-2 py-4 text-sm sm:grid-cols-[1fr_auto_auto] sm:items-center sm:gap-6"
                >
                  <div>
                    <p className="font-medium">
                      {payment.invoice_number ?? 'Gaia payment'}
                    </p>
                    <p className="text-muted-foreground mt-1 font-mono text-xs">
                      {payment.reference ?? 'Reference unavailable'}
                    </p>
                  </div>
                  <div className="sm:text-right">
                    <p className="font-semibold">{naira(payment.amount_naira)}</p>
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
  )
}
