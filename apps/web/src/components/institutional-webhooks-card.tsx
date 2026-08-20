'use client'

import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'

import { StatusPill } from '@/components/status-pill'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { formatDate, humanize } from '@/lib/format'

interface WebhookEndpoint {
  id: string
  name: string
  url: string
  enabled: boolean
  event_types: string[]
  jurisdiction_codes: string[]
  secret_version: number
  created_at: string
  disabled_at: string | null
}

interface WebhookDelivery {
  id: string
  endpoint_id: string
  fiscal_event_id: string
  status: 'pending' | 'retrying' | 'delivered' | 'dead_letter' | 'deferred'
  attempt_count: number
  next_attempt_at: string | null
  last_attempt_at: string | null
  delivered_at: string | null
  response_status: number | null
  last_error: string | null
  payload_sha256: string
  created_at: string
}

interface WebhookStatus {
  signing_configured: boolean
  delivery_enabled: boolean
  note: string
}

interface SecretResponse {
  signing_secret: string
  secret_version: number
  signing_note: string
}

const inputClass =
  'border-input bg-background focus-visible:border-ring focus-visible:ring-ring/50 h-10 w-full rounded-md border px-3 text-sm outline-none focus-visible:ring-[3px]'

const eventTypes = [
  'new_source_detected',
  'source_revised',
  'claim_superseded',
  'evidence_upgraded',
  'evidence_downgraded',
  'cross_source_conflict',
  'fiscal_state_changed',
  'faac_spike',
  'faac_decline',
]

async function errorMessage(response: Response) {
  const body = (await response.json().catch(() => ({}))) as { detail?: string }
  return body.detail ?? 'Request failed.'
}

function statusTone(status: WebhookDelivery['status']) {
  if (status === 'delivered') return 'success' as const
  if (status === 'dead_letter') return 'demo' as const
  return 'neutral' as const
}

export function InstitutionalWebhooksCard() {
  const [endpoints, setEndpoints] = useState<WebhookEndpoint[]>([])
  const [deliveries, setDeliveries] = useState<WebhookDelivery[]>([])
  const [status, setStatus] = useState<WebhookStatus | null>(null)
  const [message, setMessage] = useState('')
  const [secret, setSecret] = useState<SecretResponse | null>(null)
  const [loading, setLoading] = useState(true)

  async function load() {
    const [statusResponse, endpointResponse, deliveryResponse] =
      await Promise.all([
        fetch('/api/customer/account/webhooks/status', { cache: 'no-store' }),
        fetch('/api/customer/account/webhooks', { cache: 'no-store' }),
        fetch('/api/customer/account/webhooks/deliveries?limit=25', {
          cache: 'no-store',
        }),
      ])
    if (!endpointResponse.ok) {
      setMessage(await errorMessage(endpointResponse))
      setLoading(false)
      return
    }
    if (statusResponse.ok)
      setStatus((await statusResponse.json()) as WebhookStatus)
    setEndpoints((await endpointResponse.json()) as WebhookEndpoint[])
    if (deliveryResponse.ok) {
      setDeliveries((await deliveryResponse.json()) as WebhookDelivery[])
    }
    setLoading(false)
  }

  useEffect(() => {
    // Initial institutional-integration hydration updates local UI state.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load()
  }, [])

  async function createWebhook(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setMessage('')
    setSecret(null)
    const form = event.currentTarget
    const data = new FormData(form)
    const jurisdictions = String(data.get('jurisdictions') ?? '')
      .split(',')
      .map((value) => value.trim())
      .filter(Boolean)
    const response = await fetch('/api/customer/account/webhooks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: data.get('name'),
        url: data.get('url'),
        event_types: data.getAll('event_types'),
        jurisdiction_codes: jurisdictions,
      }),
    })
    if (!response.ok) {
      setMessage(await errorMessage(response))
      return
    }
    const body = (await response.json()) as WebhookEndpoint & SecretResponse
    setSecret(body)
    form.reset()
    await load()
  }

  async function endpointAction(id: string, action: 'enable' | 'disable') {
    setMessage('')
    const response = await fetch(
      `/api/customer/account/webhooks/${id}/${action}`,
      {
        method: 'POST',
      },
    )
    if (!response.ok) {
      setMessage(await errorMessage(response))
      return
    }
    await load()
  }

  async function rotateSecret(id: string) {
    setMessage('')
    setSecret(null)
    const response = await fetch(
      `/api/customer/account/webhooks/${id}/rotate-secret`,
      {
        method: 'POST',
      },
    )
    if (!response.ok) {
      setMessage(await errorMessage(response))
      return
    }
    setSecret((await response.json()) as SecretResponse)
    await load()
  }

  return (
    <Card className="mt-6">
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle>Institutional webhooks</CardTitle>
            <CardDescription className="mt-1 max-w-3xl">
              Route immutable Gaia Fiscal Events into your organization’s
              systems. Endpoints are HTTPS-only, signed, retried, and governed
              by your API-plan entitlement.
            </CardDescription>
          </div>
          <StatusPill tone={status?.delivery_enabled ? 'success' : 'neutral'}>
            {status?.delivery_enabled
              ? 'Delivery operational'
              : status?.signing_configured
                ? 'Configuration only'
                : 'Operator setup required'}
          </StatusPill>
        </div>
      </CardHeader>
      <CardContent className="space-y-7">
        {status ? (
          <p className="border-border bg-muted/20 rounded-md border p-3 text-xs leading-5">
            {status.note}
          </p>
        ) : null}

        {message ? (
          <p className="border-border bg-muted/30 rounded-md border p-3 text-sm">
            {message}
          </p>
        ) : null}

        {secret ? (
          <div className="border-primary/30 bg-primary/5 rounded-md border p-4">
            <p className="text-sm font-semibold">Copy signing secret now</p>
            <p className="text-muted-foreground mt-1 text-xs">
              {secret.signing_note}
            </p>
            <code className="mt-3 block text-xs break-all">
              {secret.signing_secret}
            </code>
            <p className="text-muted-foreground mt-2 text-xs">
              Secret version {secret.secret_version}. Verify
              `Gaia-Webhook-Signature` against the exact request body and reject
              stale timestamps or repeated `Gaia-Webhook-Id` values.
            </p>
          </div>
        ) : null}

        <form onSubmit={createWebhook} className="space-y-4">
          <div className="grid gap-3 md:grid-cols-2">
            <label className="grid gap-2 text-sm font-medium">
              Endpoint name
              <input
                className={inputClass}
                name="name"
                placeholder="Risk data pipeline"
                required
              />
            </label>
            <label className="grid gap-2 text-sm font-medium">
              HTTPS endpoint
              <input
                className={inputClass}
                name="url"
                type="url"
                placeholder="https://hooks.example.com/gaia"
                required
              />
            </label>
          </div>
          <label className="grid gap-2 text-sm font-medium">
            Jurisdictions (optional)
            <input
              className={inputClass}
              name="jurisdictions"
              placeholder="LA, KN, RV — leave blank for all"
            />
          </label>
          <fieldset>
            <legend className="text-sm font-medium">
              Fiscal event classes
            </legend>
            <div className="mt-2 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
              {eventTypes.map((eventType) => (
                <label
                  key={eventType}
                  className="flex items-center gap-2 text-sm"
                >
                  <input
                    type="checkbox"
                    name="event_types"
                    value={eventType}
                    defaultChecked={
                      eventType === 'source_revised' ||
                      eventType === 'cross_source_conflict' ||
                      eventType === 'fiscal_state_changed'
                    }
                  />
                  {humanize(eventType)}
                </label>
              ))}
            </div>
          </fieldset>
          <Button
            type="submit"
            disabled={status ? !status.signing_configured : false}
          >
            Create webhook
          </Button>
        </form>

        <section>
          <h3 className="text-sm font-semibold">Endpoints</h3>
          {loading ? (
            <p className="text-muted-foreground mt-3 text-sm">
              Loading integrations…
            </p>
          ) : endpoints.length === 0 ? (
            <p className="text-muted-foreground mt-3 text-sm">
              No institutional endpoints yet.
            </p>
          ) : (
            <div className="mt-3 space-y-3">
              {endpoints.map((endpoint) => (
                <div
                  key={endpoint.id}
                  className="border-border rounded-md border p-4"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="font-medium">{endpoint.name}</p>
                        <StatusPill
                          tone={endpoint.enabled ? 'success' : 'neutral'}
                        >
                          {endpoint.enabled ? 'enabled' : 'disabled'}
                        </StatusPill>
                      </div>
                      <p className="text-muted-foreground mt-1 text-xs break-all">
                        {endpoint.url}
                      </p>
                      <p className="text-muted-foreground mt-2 text-xs">
                        {endpoint.event_types.map(humanize).join(' · ')}
                      </p>
                      <p className="text-muted-foreground mt-1 text-xs">
                        {endpoint.jurisdiction_codes.length
                          ? `Jurisdictions: ${endpoint.jurisdiction_codes.join(', ')}`
                          : 'All jurisdictions'}{' '}
                        · secret v{endpoint.secret_version}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => rotateSecret(endpoint.id)}
                      >
                        Rotate secret
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          endpointAction(
                            endpoint.id,
                            endpoint.enabled ? 'disable' : 'enable',
                          )
                        }
                      >
                        {endpoint.enabled ? 'Disable' : 'Enable'}
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section>
          <div className="flex flex-wrap items-end justify-between gap-2">
            <h3 className="text-sm font-semibold">Recent delivery ledger</h3>
            <span className="text-muted-foreground text-xs">
              Latest 25 deliveries
            </span>
          </div>
          {deliveries.length === 0 ? (
            <p className="text-muted-foreground mt-3 text-sm">
              No webhook deliveries have been materialized yet.
            </p>
          ) : (
            <div className="mt-3 space-y-3">
              {deliveries.map((delivery) => (
                <div
                  key={delivery.id}
                  className="border-border grid gap-3 rounded-md border p-4 text-xs md:grid-cols-[9rem_1fr_auto]"
                >
                  <div>
                    <StatusPill tone={statusTone(delivery.status)}>
                      {delivery.status}
                    </StatusPill>
                    <p className="text-muted-foreground mt-2">
                      {formatDate(delivery.created_at.slice(0, 10))}
                    </p>
                  </div>
                  <div className="min-w-0">
                    <p className="font-mono font-medium break-all">
                      {delivery.fiscal_event_id}
                    </p>
                    <p className="text-muted-foreground mt-1 font-mono break-all">
                      SHA-256 {delivery.payload_sha256}
                    </p>
                    {delivery.last_error ? (
                      <p className="text-muted-foreground mt-2">
                        {delivery.last_error}
                      </p>
                    ) : null}
                  </div>
                  <div className="text-muted-foreground md:text-right">
                    <p>{delivery.attempt_count} attempts</p>
                    <p className="mt-1">
                      {delivery.response_status
                        ? `HTTP ${delivery.response_status}`
                        : 'No response'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </CardContent>
    </Card>
  )
}
