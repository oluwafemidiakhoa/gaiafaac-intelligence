'use client'

import { BellRing, Mail, ShieldCheck } from 'lucide-react'
import { useEffect, useState } from 'react'

import { StatusPill } from '@/components/status-pill'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

interface NotificationPreference {
  email_enabled: boolean
  include_fiscal_watch: boolean
  include_fiscal_events: boolean
  email_enabled_at: string | null
  delivery_available: boolean
  delivery_note: string
}

async function errorMessage(response: Response) {
  const body = (await response.json().catch(() => ({}))) as { detail?: string }
  return body.detail ?? 'Request failed.'
}

export function NotificationPreferencesCard() {
  const [preference, setPreference] = useState<NotificationPreference | null>(
    null,
  )
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    async function load() {
      const response = await fetch('/api/customer/watchlists/preferences', {
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
      setPreference((await response.json()) as NotificationPreference)
    }
    void load()
  }, [])

  async function save(next: NotificationPreference) {
    setSaving(true)
    setMessage('')
    const response = await fetch('/api/customer/watchlists/preferences', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email_enabled: next.email_enabled,
        include_fiscal_watch: next.include_fiscal_watch,
        include_fiscal_events: next.include_fiscal_events,
      }),
    })
    if (!response.ok) {
      setMessage(await errorMessage(response))
      setSaving(false)
      return
    }
    setPreference((await response.json()) as NotificationPreference)
    setMessage('Notification preferences saved.')
    setSaving(false)
  }

  if (!preference) {
    return message ? (
      <p className="border-border bg-muted/30 mt-8 rounded-lg border p-3 text-sm">
        {message}
      </p>
    ) : null
  }

  return (
    <Card className="mt-8">
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <span className="bg-primary/10 text-primary flex size-10 shrink-0 items-center justify-center rounded-lg">
              <BellRing className="size-5" aria-hidden="true" />
            </span>
            <div>
              <CardTitle>Alert delivery</CardTitle>
              <CardDescription className="mt-1 max-w-3xl">
                Inbox alerts are always governed by your Watchlist. Email is a
                separate, explicit opt-in and can be disabled at any time.
              </CardDescription>
            </div>
          </div>
          <StatusPill
            tone={preference.delivery_available ? 'success' : 'neutral'}
          >
            {preference.delivery_available ? 'Email operational' : 'Inbox only'}
          </StatusPill>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        <label className="border-border flex cursor-pointer items-start gap-3 rounded-lg border p-4">
          <input
            type="checkbox"
            className="mt-1 size-4"
            checked={preference.email_enabled}
            onChange={(event) =>
              setPreference({
                ...preference,
                email_enabled: event.target.checked,
              })
            }
          />
          <span>
            <span className="flex items-center gap-2 font-medium">
              <Mail className="size-4" aria-hidden="true" /> Email my governed
              alerts
            </span>
            <span className="text-muted-foreground mt-1 block text-sm leading-6">
              Send alerts to the email address on this GaiaFAAC account.
              Delivery occurs only when the platform operator has enabled the
              outbound channel.
            </span>
          </span>
        </label>

        <div className="grid gap-3 md:grid-cols-2">
          <label className="border-border flex cursor-pointer items-start gap-3 rounded-lg border p-4">
            <input
              type="checkbox"
              className="mt-1 size-4"
              checked={preference.include_fiscal_watch}
              onChange={(event) =>
                setPreference({
                  ...preference,
                  include_fiscal_watch: event.target.checked,
                })
              }
            />
            <span>
              <span className="font-medium">Allocation signals</span>
              <span className="text-muted-foreground mt-1 block text-sm leading-6">
                Large monthly moves, negative net allocations and high deduction
                burden.
              </span>
            </span>
          </label>
          <label className="border-border flex cursor-pointer items-start gap-3 rounded-lg border p-4">
            <input
              type="checkbox"
              className="mt-1 size-4"
              checked={preference.include_fiscal_events}
              onChange={(event) =>
                setPreference({
                  ...preference,
                  include_fiscal_events: event.target.checked,
                })
              }
            />
            <span>
              <span className="font-medium">Evidence lifecycle</span>
              <span className="text-muted-foreground mt-1 block text-sm leading-6">
                Source revisions, superseded claims, evidence changes, conflicts
                and Fiscal State changes.
              </span>
            </span>
          </label>
        </div>

        <div className="bg-muted/25 flex items-start gap-3 rounded-lg p-4 text-sm">
          <ShieldCheck
            className="text-primary mt-0.5 size-4 shrink-0"
            aria-hidden="true"
          />
          <p className="text-muted-foreground leading-6">
            {preference.delivery_note}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={() => save(preference)} disabled={saving}>
            {saving ? 'Saving…' : 'Save alert delivery'}
          </Button>
          {message ? (
            <span className="text-muted-foreground text-sm">{message}</span>
          ) : null}
        </div>
      </CardContent>
    </Card>
  )
}
