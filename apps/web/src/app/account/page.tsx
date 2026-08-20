'use client'

import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'

import { InstitutionalWebhooksCard } from '@/components/institutional-webhooks-card'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

interface Profile {
  user_id: string
  full_name: string
  email: string
  organization_id: string
  organization_name: string
  membership_role: 'owner' | 'admin' | 'member'
  plan_code: string
  subscription_status: string | null
  historical_access: boolean
  downloads: boolean
  api_access: boolean
  max_users: number
}

interface Member {
  user_id: string
  full_name: string
  email: string
  role: string
}

interface ApiKeyItem {
  id: string
  name: string
  key_prefix: string
  last_used_at: string | null
  revoked_at: string | null
}

const inputClass =
  'border-input bg-background focus-visible:border-ring focus-visible:ring-ring/50 h-10 w-full rounded-md border px-3 text-sm outline-none focus-visible:ring-[3px]'

async function errorMessage(response: Response) {
  const body = (await response.json().catch(() => ({}))) as {
    detail?: string
    error?: string
  }
  return body.detail ?? body.error ?? 'Request failed.'
}

function requestedPlan() {
  return new URLSearchParams(window.location.search).get('plan')
}

export default function AccountPage() {
  const [profile, setProfile] = useState<Profile | null>(null)
  const [members, setMembers] = useState<Member[]>([])
  const [keys, setKeys] = useState<ApiKeyItem[]>([])
  const [message, setMessage] = useState('')
  const [revealedKey, setRevealedKey] = useState('')
  const [loading, setLoading] = useState(true)

  async function load() {
    const response = await fetch('/api/customer/account/me', {
      cache: 'no-store',
    })
    if (response.status === 401) {
      const plan = requestedPlan()
      window.location.assign(
        plan
          ? `/account/login?plan=${encodeURIComponent(plan)}`
          : '/account/login',
      )
      return
    }
    if (!response.ok) {
      setMessage(await errorMessage(response))
      setLoading(false)
      return
    }
    const nextProfile = (await response.json()) as Profile
    setProfile(nextProfile)
    if (nextProfile.membership_role !== 'member') {
      const membersResponse = await fetch(
        '/api/customer/account/team/members',
        {
          cache: 'no-store',
        },
      )
      if (membersResponse.ok)
        setMembers((await membersResponse.json()) as Member[])
    }
    if (nextProfile.api_access) {
      const keysResponse = await fetch('/api/customer/account/api-keys', {
        cache: 'no-store',
      })
      if (keysResponse.ok) setKeys((await keysResponse.json()) as ApiKeyItem[])
    }
    setLoading(false)
  }

  useEffect(() => {
    // Initial account hydration is intentionally asynchronous and updates local UI state.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load()
  }, [])

  async function checkout(planCode: string) {
    setMessage('')
    const response = await fetch('/api/customer/billing/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ plan_code: planCode }),
    })
    if (!response.ok) {
      setMessage(await errorMessage(response))
      return
    }
    const body = (await response.json()) as { url: string }
    window.location.assign(body.url)
  }

  async function manageBilling() {
    setMessage('')
    const response = await fetch('/api/customer/billing/portal', {
      method: 'POST',
    })
    if (!response.ok) {
      setMessage(await errorMessage(response))
      return
    }
    const body = (await response.json()) as { url: string }
    window.location.assign(body.url)
  }

  async function invite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setMessage('')
    const form = event.currentTarget
    const data = new FormData(form)
    const response = await fetch('/api/customer/account/team/invites', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: data.get('email'),
        full_name: data.get('full_name'),
        role: data.get('role'),
      }),
    })
    if (!response.ok) {
      setMessage(await errorMessage(response))
      return
    }
    form.reset()
    setMessage('Invitation sent.')
  }

  async function createKey(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setMessage('')
    setRevealedKey('')
    const form = event.currentTarget
    const data = new FormData(form)
    const response = await fetch('/api/customer/account/api-keys', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: data.get('name') }),
    })
    if (!response.ok) {
      setMessage(await errorMessage(response))
      return
    }
    const body = (await response.json()) as ApiKeyItem & { api_key: string }
    setRevealedKey(body.api_key)
    form.reset()
    await load()
  }

  async function revokeKey(id: string) {
    const response = await fetch(`/api/customer/account/api-keys/${id}`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      setMessage(await errorMessage(response))
      return
    }
    await load()
  }

  async function removeMember(id: string) {
    const response = await fetch(`/api/customer/account/team/members/${id}`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      setMessage(await errorMessage(response))
      return
    }
    await load()
  }

  async function logout() {
    await fetch('/api/customer/account/logout', { method: 'POST' })
    window.location.assign('/')
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-7xl px-5 py-16 text-sm">
        Loading account…
      </div>
    )
  }
  if (!profile) {
    return (
      <div className="mx-auto max-w-7xl px-5 py-16">
        <p className="text-destructive text-sm font-medium">
          {message || 'Account unavailable.'}
        </p>
      </div>
    )
  }

  const canAdmin = profile.membership_role !== 'member'

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-primary font-mono text-xs font-semibold tracking-[0.18em] uppercase">
            Customer workspace
          </p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight">
            {profile.organization_name}
          </h1>
          <p className="text-muted-foreground mt-2 text-sm">
            {profile.full_name} · {profile.email}
          </p>
        </div>
        <Button variant="outline" onClick={logout}>
          Sign out
        </Button>
      </div>

      {message ? (
        <p className="border-border bg-muted/30 mt-6 rounded-md border p-3 text-sm">
          {message}
        </p>
      ) : null}

      <div className="mt-8 grid gap-5 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Plan</CardTitle>
            <CardDescription>Current organization entitlement</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold capitalize">
              {profile.plan_code}
            </p>
            <p className="text-muted-foreground mt-2 text-sm">
              {profile.subscription_status ?? 'No paid subscription'}
            </p>
            {profile.subscription_status ? (
              <Button className="mt-5" onClick={manageBilling}>
                Manage billing
              </Button>
            ) : (
              <div className="mt-5 flex flex-wrap gap-2">
                {['analyst', 'team', 'api'].map((plan) => (
                  <Button
                    key={plan}
                    variant="outline"
                    onClick={() => checkout(plan)}
                  >
                    Start {plan}
                  </Button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Data access</CardTitle>
            <CardDescription>Entitlements enforced by the API</CardDescription>
          </CardHeader>
          <CardContent className="text-sm">
            <p>
              Historical access:{' '}
              {profile.historical_access ? 'Enabled' : 'Free tier only'}
            </p>
            <p className="mt-2">
              Downloads: {profile.downloads ? 'Enabled' : 'Not included'}
            </p>
            <p className="mt-2">
              API: {profile.api_access ? 'Enabled' : 'Not included'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Organization</CardTitle>
            <CardDescription>Team capacity and role</CardDescription>
          </CardHeader>
          <CardContent className="text-sm">
            <p className="capitalize">Your role: {profile.membership_role}</p>
            <p className="mt-2">Member limit: {profile.max_users}</p>
          </CardContent>
        </Card>
      </div>

      {profile.downloads ? (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Self-service exports</CardTitle>
            <CardDescription>
              Download a published month with source fingerprint preserved in
              the export.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form
              className="flex flex-wrap items-end gap-3"
              onSubmit={(event) => {
                event.preventDefault()
                const data = new FormData(event.currentTarget)
                const month = String(data.get('month') ?? '')
                if (!month) return
                const format = String(data.get('format') ?? 'csv')
                window.location.assign(
                  `/api/customer/account/exports/allocations.${format}?month=${month}-01`,
                )
              }}
            >
              <label className="grid gap-2 text-sm font-medium">
                Published month
                <input
                  className={inputClass}
                  type="month"
                  name="month"
                  required
                />
              </label>
              <label className="grid gap-2 text-sm font-medium">
                Format
                <select
                  className={inputClass}
                  name="format"
                  defaultValue="xlsx"
                >
                  <option value="xlsx">Excel workbook</option>
                  <option value="csv">CSV</option>
                </select>
              </label>
              <Button type="submit">Download</Button>
            </form>
          </CardContent>
        </Card>
      ) : null}

      {canAdmin && profile.max_users > 1 ? (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Team administration</CardTitle>
            <CardDescription>
              Invite members by email and remove non-owner members from this
              organization.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={invite} className="grid gap-3 md:grid-cols-4">
              <input
                className={inputClass}
                name="full_name"
                placeholder="Full name"
              />
              <input
                className={inputClass}
                name="email"
                type="email"
                placeholder="Work email"
                required
              />
              <select className={inputClass} name="role" defaultValue="member">
                <option value="member">Member</option>
                <option value="admin">Administrator</option>
              </select>
              <Button type="submit">Send invitation</Button>
            </form>
            <div className="mt-6 space-y-3">
              {members.map((member) => (
                <div
                  key={member.user_id}
                  className="border-border flex flex-wrap items-center justify-between gap-3 border-t pt-3 text-sm"
                >
                  <div>
                    <p className="font-medium">{member.full_name}</p>
                    <p className="text-muted-foreground">
                      {member.email} · {member.role}
                    </p>
                  </div>
                  {member.user_id !== profile.user_id &&
                  member.role !== 'owner' ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => removeMember(member.user_id)}
                    >
                      Remove
                    </Button>
                  ) : null}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : null}

      {profile.api_access && canAdmin ? (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>API keys</CardTitle>
            <CardDescription>
              Create keys for published historical endpoints. Plaintext keys are
              shown once.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form
              onSubmit={createKey}
              className="flex flex-wrap items-end gap-3"
            >
              <label className="grid gap-2 text-sm font-medium">
                Key name
                <input
                  className={inputClass}
                  name="name"
                  placeholder="Production"
                  required
                />
              </label>
              <Button type="submit">Create API key</Button>
            </form>
            {revealedKey ? (
              <div className="border-primary/30 bg-primary/5 mt-5 rounded-md border p-4">
                <p className="text-sm font-medium">
                  Copy this key now. It will not be shown again.
                </p>
                <code className="mt-2 block text-xs break-all">
                  {revealedKey}
                </code>
              </div>
            ) : null}
            <div className="mt-6 space-y-3">
              {keys.map((key) => (
                <div
                  key={key.id}
                  className="border-border flex flex-wrap items-center justify-between gap-3 border-t pt-3 text-sm"
                >
                  <div>
                    <p className="font-medium">{key.name}</p>
                    <p className="text-muted-foreground font-mono text-xs">
                      {key.key_prefix}…
                    </p>
                  </div>
                  {!key.revoked_at ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => revokeKey(key.id)}
                    >
                      Revoke
                    </Button>
                  ) : (
                    <span className="text-muted-foreground text-xs">
                      Revoked
                    </span>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : null}

      {profile.api_access && canAdmin ? <InstitutionalWebhooksCard /> : null}
    </div>
  )
}
