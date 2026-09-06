'use client'

import {
  CheckCircle2,
  FileCheck2,
  FileJson2,
  FileSpreadsheet,
  FileText,
  Loader2,
  PackageCheck,
  ShieldCheck,
} from 'lucide-react'
import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

interface CommercialProduct {
  code: string
  label: string
  billing_mode: string
  description: string
  price_naira: number | null
}

interface Purchase {
  id: string
  product_code: string
  amount_naira: string
  currency: string
  status: string
  fulfillment_status: string
  fulfillment_reference: string | null
  completed_at: string | null
  created_at: string
}

type ProductCode =
  | 'decision_pack'
  | 'multi_state_comparison_pack'
  | 'historical_evidence_export'
  | 'due_diligence_snapshot'

async function errorMessage(response: Response) {
  const body = (await response.json().catch(() => ({}))) as {
    detail?: string
    error?: string
  }
  return body.detail ?? body.error ?? 'Request failed.'
}

function naira(value: number | string | null) {
  if (value === null) return 'Price unavailable'
  const amount = Number(value)
  if (!Number.isFinite(amount)) return `₦${value}`
  return new Intl.NumberFormat('en-NG', {
    style: 'currency',
    currency: 'NGN',
    maximumFractionDigits: 0,
  }).format(amount)
}

export default function ProjectProductsPage() {
  const [products, setProducts] = useState<CommercialProduct[]>([])
  const [purchases, setPurchases] = useState<Purchase[]>([])
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [buying, setBuying] = useState<ProductCode | null>(null)
  const [selected, setSelected] = useState<ProductCode>('decision_pack')
  const [state, setState] = useState('lagos')
  const [states, setStates] = useState('lagos, rivers')
  const [year, setYear] = useState('2026')
  const [domain, setDomain] = useState('igr')
  const [startYear, setStartYear] = useState('2023')
  const [endYear, setEndYear] = useState('2026')

  const oneTimeProducts = useMemo(
    () => products.filter((product) => product.billing_mode === 'one_time'),
    [products],
  )

  async function loadPurchases() {
    const response = await fetch('/api/customer/billing/one-time/purchases', {
      cache: 'no-store',
    })
    if (response.status === 401) return
    if (!response.ok) {
      setMessage(await errorMessage(response))
      return
    }
    setPurchases((await response.json()) as Purchase[])
  }

  async function verifyReturnedPurchase() {
    const params = new URLSearchParams(window.location.search)
    if (params.get('purchase') !== 'return') return
    const reference = params.get('reference') ?? params.get('trxref')
    if (!reference) {
      setMessage('Paystack returned without a purchase reference.')
      return
    }
    const response = await fetch(
      `/api/customer/billing/one-time/paystack-verify?reference=${encodeURIComponent(reference)}`,
      { method: 'POST' },
    )
    if (!response.ok) {
      setMessage(await errorMessage(response))
      return
    }
    const purchase = (await response.json()) as Purchase
    setMessage(
      purchase.fulfillment_status === 'ready'
        ? 'Payment confirmed. Your governed intelligence package is ready in PDF, Excel and JSON.'
        : 'Payment confirmed. Gaia is preparing your governed intelligence package.',
    )
    window.history.replaceState({}, '', '/projects')
  }

  useEffect(() => {
    void (async () => {
      const productsResponse = await fetch('/api/customer/commercial/products', {
        cache: 'no-store',
      })
      if (productsResponse.ok) {
        setProducts((await productsResponse.json()) as CommercialProduct[])
      }
      await verifyReturnedPurchase()
      await loadPurchases()
      setLoading(false)
    })()
  }, [])

  function contextFor(productCode: ProductCode) {
    if (productCode === 'multi_state_comparison_pack') {
      return {
        states: states
          .split(',')
          .map((value) => value.trim())
          .filter(Boolean),
        year: Number(year),
      }
    }
    if (productCode === 'historical_evidence_export') {
      return {
        state,
        domain,
        start_year: Number(startYear),
        end_year: Number(endYear),
      }
    }
    return { state, year: Number(year) }
  }

  async function buy(productCode: ProductCode) {
    setBuying(productCode)
    setMessage('')
    const response = await fetch('/api/customer/billing/one-time/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        product_code: productCode,
        context: contextFor(productCode),
      }),
    })
    if (response.status === 401) {
      window.location.assign('/account/login?next=/projects')
      return
    }
    if (!response.ok) {
      setMessage(await errorMessage(response))
      setBuying(null)
      return
    }
    const body = (await response.json()) as { url: string }
    window.location.assign(body.url)
  }

  if (loading) {
    return (
      <div className="gaia-shell gaia-section flex min-h-64 items-center justify-center">
        <Loader2 className="text-primary size-6 animate-spin" />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <div className="max-w-3xl">
        <p className="text-primary text-xs font-semibold tracking-[0.18em] uppercase">
          Governed fiscal intelligence · one-time engagement
        </p>
        <h1 className="mt-3 text-4xl font-semibold tracking-[-0.04em] sm:text-5xl">
          Project Products
        </h1>
        <p className="text-muted-foreground mt-4 text-base leading-7">
          You are buying a governed fiscal-intelligence result for a defined
          jurisdiction, period and evidence boundary — not a file format. Gaia
          validates the evidence before checkout, freezes the governed result to
          the order, and includes PDF, Excel and JSON as delivery formats.
        </p>
      </div>

      <Card className="border-primary/30 bg-primary/[0.035] mt-8">
        <CardContent className="flex gap-4 py-5">
          <ShieldCheck className="text-primary mt-0.5 size-5 shrink-0" />
          <div>
            <p className="font-semibold">What the price covers</p>
            <p className="text-muted-foreground mt-1 text-sm leading-6">
              Evidence selection, governed-source validation, provenance,
              jurisdiction/period scoping, deterministic calculations and the
              resulting intelligence package. PDF, Excel and JSON are included
              representations of the same paid evidence product.
            </p>
          </div>
        </CardContent>
      </Card>

      <div className="mt-8 grid gap-4 md:grid-cols-3">
        <Card className="border-primary/25 bg-primary/[0.03]">
          <CardContent className="py-5">
            <PackageCheck className="text-primary size-5" />
            <p className="mt-3 font-semibold">1. Define the decision boundary</p>
            <p className="text-muted-foreground mt-1 text-sm leading-6">
              Choose the jurisdiction, period and evidence scope the analysis
              must answer.
            </p>
          </CardContent>
        </Card>
        <Card className="border-primary/25 bg-primary/[0.03]">
          <CardContent className="py-5">
            <CheckCircle2 className="text-primary size-5" />
            <p className="mt-3 font-semibold">2. Gaia validates and freezes</p>
            <p className="text-muted-foreground mt-1 text-sm leading-6">
              Gaia refuses unsupported evidence boundaries and freezes the
              governed result to the paid order.
            </p>
          </CardContent>
        </Card>
        <Card className="border-primary/25 bg-primary/[0.03]">
          <CardContent className="py-5">
            <FileSpreadsheet className="text-primary size-5" />
            <p className="mt-3 font-semibold">
              3. Receive the intelligence package
            </p>
            <p className="text-muted-foreground mt-1 text-sm leading-6">
              PDF for review, Excel for analysis and JSON for machine use are
              included delivery formats — not separate products.
            </p>
          </CardContent>
        </Card>
      </div>

      {message ? (
        <div className="border-border bg-muted/30 mt-8 rounded-2xl border p-4 text-sm">
          {message}
        </div>
      ) : null}

      <div className="mt-10 grid gap-4 lg:grid-cols-4">
        {oneTimeProducts.map((product) => (
          <button
            key={product.code}
            type="button"
            onClick={() => setSelected(product.code as ProductCode)}
            className="text-left"
          >
            <Card
              className={
                selected === product.code ? 'border-primary/60 shadow-sm' : ''
              }
            >
              <CardHeader>
                <FileCheck2 className="text-primary size-5" />
                <CardTitle className="pt-3 text-lg">{product.label}</CardTitle>
                <CardDescription>{product.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-xl font-semibold">
                  {naira(product.price_naira)}
                </p>
                <p className="text-muted-foreground mt-1 text-xs">
                  one-time intelligence engagement · all delivery formats included
                </p>
              </CardContent>
            </Card>
          </button>
        ))}
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Define the evidence boundary</CardTitle>
          <CardDescription>
            Gaia will refuse checkout rather than charge for an evidence
            boundary it cannot currently support.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          {selected === 'multi_state_comparison_pack' ? (
            <label className="block text-sm font-medium">
              Jurisdictions (2–6, comma separated)
              <input
                value={states}
                onChange={(event) => setStates(event.target.value)}
                className="border-input bg-background mt-2 w-full rounded-xl border px-3 py-2.5 font-normal"
                placeholder="lagos, rivers, kano"
              />
            </label>
          ) : (
            <label className="block text-sm font-medium">
              Jurisdiction
              <input
                value={state}
                onChange={(event) => setState(event.target.value)}
                className="border-input bg-background mt-2 w-full rounded-xl border px-3 py-2.5 font-normal"
                placeholder="lagos or LA"
              />
            </label>
          )}

          {selected === 'historical_evidence_export' ? (
            <div className="grid gap-4 sm:grid-cols-3">
              <label className="block text-sm font-medium">
                Evidence lane
                <select
                  value={domain}
                  onChange={(event) => setDomain(event.target.value)}
                  className="border-input bg-background mt-2 w-full rounded-xl border px-3 py-2.5 font-normal"
                >
                  <option value="igr">State IGR</option>
                  <option value="faac">FAAC allocation</option>
                </select>
              </label>
              <label className="block text-sm font-medium">
                Start year
                <input
                  type="number"
                  value={startYear}
                  onChange={(event) => setStartYear(event.target.value)}
                  className="border-input bg-background mt-2 w-full rounded-xl border px-3 py-2.5 font-normal"
                />
              </label>
              <label className="block text-sm font-medium">
                End year
                <input
                  type="number"
                  value={endYear}
                  onChange={(event) => setEndYear(event.target.value)}
                  className="border-input bg-background mt-2 w-full rounded-xl border px-3 py-2.5 font-normal"
                />
              </label>
            </div>
          ) : (
            <label className="block text-sm font-medium">
              Evidence year
              <input
                type="number"
                value={year}
                onChange={(event) => setYear(event.target.value)}
                className="border-input bg-background mt-2 w-full rounded-xl border px-3 py-2.5 font-normal sm:max-w-xs"
              />
            </label>
          )}

          <Button
            onClick={() => void buy(selected)}
            disabled={buying !== null}
            size="lg"
          >
            {buying === selected ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <PackageCheck className="size-4" />
            )}
            {buying === selected
              ? 'Checking evidence…'
              : 'Check evidence & buy intelligence'}
          </Button>
        </CardContent>
      </Card>

      <section className="mt-12" aria-labelledby="project-orders">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-primary text-xs font-semibold tracking-[0.18em] uppercase">
              Your project orders
            </p>
            <h2 id="project-orders" className="mt-2 text-2xl font-semibold">
              Paid intelligence stays tied to your organization.
            </h2>
            <p className="text-muted-foreground mt-2 max-w-2xl text-sm leading-6">
              After payment is confirmed and fulfillment is ready, retrieve the
              same governed intelligence as PDF, Excel or JSON. The price is for
              the evidence product and decision boundary, not for choosing a
              document format.
            </p>
          </div>
          <Button asChild variant="outline">
            <Link href="/account/billing">Billing history</Link>
          </Button>
        </div>

        {purchases.length === 0 ? (
          <p className="text-muted-foreground mt-5 text-sm">
            No one-time project orders have been created for this organization.
          </p>
        ) : (
          <div className="mt-5 space-y-4">
            {purchases.map((purchase) => (
              <Card key={purchase.id}>
                <CardContent className="flex flex-wrap items-center justify-between gap-4 py-5">
                  <div>
                    <div className="flex items-center gap-2">
                      {purchase.fulfillment_status === 'ready' ? (
                        <CheckCircle2 className="size-4 text-emerald-600" />
                      ) : null}
                      <p className="font-semibold">
                        {purchase.product_code.replaceAll('_', ' ')}
                      </p>
                    </div>
                    <p className="text-muted-foreground mt-1 text-sm">
                      {naira(purchase.amount_naira)} · payment {purchase.status} ·
                      intelligence {purchase.fulfillment_status}
                    </p>
                  </div>
                  {purchase.status === 'success' &&
                  purchase.fulfillment_status === 'ready' ? (
                    <div className="flex flex-wrap gap-2">
                      <Button asChild>
                        <a
                          href={`/api/customer/billing/one-time/purchases/${purchase.id}/download.pdf`}
                        >
                          <FileText className="size-4" />
                          PDF package
                        </a>
                      </Button>
                      <Button asChild variant="outline">
                        <a
                          href={`/api/customer/billing/one-time/purchases/${purchase.id}/download.xlsx`}
                        >
                          <FileSpreadsheet className="size-4" />
                          Excel analysis
                        </a>
                      </Button>
                      <Button asChild variant="outline">
                        <Link
                          href={`/verify/project/${purchase.id}`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          <ShieldCheck className="size-4" />
                          Verify receipt
                        </Link>
                      </Button>
                      <Button asChild variant="ghost">
                        <a
                          href={`/api/customer/billing/one-time/purchases/${purchase.id}/fulfillment`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          <FileJson2 className="size-4" />
                          JSON evidence
                        </a>
                      </Button>
                    </div>
                  ) : null}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
