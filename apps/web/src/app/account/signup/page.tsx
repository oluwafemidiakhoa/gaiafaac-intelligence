'use client'

import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { useState } from 'react'
import type { FormEvent } from 'react'

import { Button } from '@/components/ui/button'

const inputClass =
  'border-input bg-background focus-visible:border-ring focus-visible:ring-ring/50 h-10 w-full rounded-md border px-3 text-sm outline-none focus-visible:ring-[3px]'

export default function AccountSignupPage() {
  const searchParams = useSearchParams()
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    const data = new FormData(event.currentTarget)
    const response = await fetch('/api/customer/account/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        full_name: data.get('full_name'),
        email: data.get('email'),
        password: data.get('password'),
        organization_name: data.get('organization_name'),
      }),
    })
    if (!response.ok) {
      const body = (await response.json().catch(() => ({}))) as {
        detail?: string
      }
      setError(body.detail ?? 'Unable to create your account.')
      setSubmitting(false)
      return
    }
    const plan = searchParams.get('plan')
    window.location.assign(
      plan ? `/account?plan=${encodeURIComponent(plan)}` : '/account',
    )
  }

  return (
    <div className="mx-auto max-w-lg px-5 py-16">
      <p className="text-primary font-mono text-xs font-semibold tracking-[0.18em] uppercase">
        Self-service access
      </p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight">
        Create your GaiaFAAC account
      </h1>
      <p className="text-muted-foreground mt-3 text-sm leading-6">
        Start on the free public tier, then activate Analyst, Team, or API
        access from your account.
      </p>
      <form onSubmit={submit} className="mt-8 grid gap-5">
        <label className="grid gap-2 text-sm font-medium">
          Full name
          <input
            className={inputClass}
            name="full_name"
            required
            minLength={2}
          />
        </label>
        <label className="grid gap-2 text-sm font-medium">
          Work email
          <input className={inputClass} name="email" type="email" required />
        </label>
        <label className="grid gap-2 text-sm font-medium">
          Organization
          <input
            className={inputClass}
            name="organization_name"
            required
            minLength={2}
          />
        </label>
        <label className="grid gap-2 text-sm font-medium">
          Password
          <input
            className={inputClass}
            name="password"
            type="password"
            required
            minLength={12}
            autoComplete="new-password"
          />
          <span className="text-muted-foreground text-xs">
            Use at least 12 characters.
          </span>
        </label>
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Creating account…' : 'Create account'}
        </Button>
        {error ? (
          <p className="text-destructive text-sm font-medium">{error}</p>
        ) : null}
      </form>
      <p className="text-muted-foreground mt-6 text-sm">
        Already have an account?{' '}
        <Link
          className="text-foreground font-medium hover:underline"
          href="/account/login"
        >
          Sign in
        </Link>
      </p>
    </div>
  )
}
