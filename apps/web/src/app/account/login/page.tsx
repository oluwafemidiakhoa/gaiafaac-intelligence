'use client'

import Link from 'next/link'
import { useState } from 'react'
import type { FormEvent } from 'react'

import { Button } from '@/components/ui/button'

const inputClass =
  'border-input bg-background focus-visible:border-ring focus-visible:ring-ring/50 h-10 w-full rounded-md border px-3 text-sm outline-none focus-visible:ring-[3px]'

function requestedPlan() {
  return new URLSearchParams(window.location.search).get('plan')
}

export default function AccountLoginPage() {
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    const data = new FormData(event.currentTarget)
    const response = await fetch('/api/customer/account/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: data.get('email'),
        password: data.get('password'),
      }),
    })
    if (!response.ok) {
      const body = (await response.json().catch(() => ({}))) as {
        detail?: string
      }
      setError(body.detail ?? 'Unable to sign in.')
      setSubmitting(false)
      return
    }
    const plan = requestedPlan()
    window.location.assign(
      plan ? `/account?plan=${encodeURIComponent(plan)}` : '/account',
    )
  }

  return (
    <div className="mx-auto max-w-md px-5 py-16">
      <p className="text-primary font-mono text-xs font-semibold tracking-[0.18em] uppercase">
        Customer account
      </p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight">
        Sign in to GaiaFAAC
      </h1>
      <p className="text-muted-foreground mt-3 text-sm leading-6">
        Manage your subscription, exports, API keys, and organization members.
      </p>
      <form onSubmit={submit} className="mt-8 grid gap-5">
        <label className="grid gap-2 text-sm font-medium">
          Work email
          <input className={inputClass} name="email" type="email" required />
        </label>
        <label className="grid gap-2 text-sm font-medium">
          Password
          <input
            className={inputClass}
            name="password"
            type="password"
            required
          />
        </label>
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Signing in…' : 'Sign in'}
        </Button>
        {error ? (
          <p className="text-destructive text-sm font-medium">{error}</p>
        ) : null}
      </form>
      <p className="text-muted-foreground mt-6 text-sm">
        New to GaiaFAAC?{' '}
        <Link
          className="text-foreground font-medium hover:underline"
          href="/account/signup"
        >
          Create an account
        </Link>
      </p>
    </div>
  )
}
