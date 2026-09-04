'use client'

import { useState } from 'react'
import type { FormEvent } from 'react'

import { Button } from '@/components/ui/button'

const fieldClass =
  'border-input bg-background placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 h-10 w-full rounded-md border px-3 text-sm outline-none focus-visible:ring-[3px]'
const textAreaClass = `${fieldClass} min-h-28 py-2`

export function PilotLeadForm() {
  const [status, setStatus] = useState<
    'idle' | 'submitting' | 'success' | 'error'
  >('idle')
  const [message, setMessage] = useState('')

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setStatus('submitting')
    setMessage('')

    const form = event.currentTarget
    const data = new FormData(form)
    const users = String(data.get('expected_users') ?? '').trim()
    const payload = {
      name: data.get('name'),
      email: data.get('email'),
      organization: data.get('organization'),
      role: data.get('role'),
      country: data.get('country'),
      plan_interest: data.get('plan_interest'),
      use_case: data.get('use_case'),
      states_or_periods: data.get('states_or_periods'),
      requested_evidence_domains: data.get('requested_evidence_domains'),
      preferred_format: data.get('preferred_format'),
      expected_users: users ? Number(users) : null,
      buying_timeline: data.get('buying_timeline'),
      source_page: '/pilot',
      website: data.get('website'),
    }

    try {
      const response = await fetch('/api/pilot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const body = (await response.json()) as {
        error?: string
        message?: string
      }
      if (!response.ok) {
        throw new Error(body.error ?? 'Unable to submit your request.')
      }
      form.reset()
      setStatus('success')
      setMessage(
        body.message ??
          'Your request has been received. We will review coverage and contact you.',
      )
    } catch (error) {
      setStatus('error')
      setMessage(
        error instanceof Error
          ? error.message
          : 'Unable to submit your request.',
      )
    }
  }

  return (
    <form onSubmit={submit} className="grid gap-5" noValidate>
      <div className="grid gap-5 sm:grid-cols-2">
        <label className="grid gap-2 text-sm font-medium">
          Name
          <input className={fieldClass} name="name" required minLength={2} />
        </label>
        <label className="grid gap-2 text-sm font-medium">
          Work email
          <input className={fieldClass} name="email" type="email" required />
        </label>
        <label className="grid gap-2 text-sm font-medium">
          Organization
          <input className={fieldClass} name="organization" />
        </label>
        <label className="grid gap-2 text-sm font-medium">
          Role
          <input className={fieldClass} name="role" />
        </label>
        <label className="grid gap-2 text-sm font-medium">
          Country
          <input className={fieldClass} name="country" />
        </label>
        <label className="grid gap-2 text-sm font-medium">
          Commercial path
          <select
            className={fieldClass}
            name="plan_interest"
            defaultValue="analyst"
          >
            <option value="analyst">Analyst Pilot</option>
            <option value="team">Team / Institutional Pilot</option>
            <option value="api">API / Data Evaluation</option>
          </select>
        </label>
      </div>

      <label className="grid gap-2 text-sm font-medium">
        Decision or workflow you need to support
        <textarea
          className={textAreaClass}
          name="use_case"
          required
          minLength={20}
          placeholder="Describe the lending, diligence, monitoring, research, audit, advisory, or integration workflow."
        />
      </label>

      <div className="grid gap-5 sm:grid-cols-2">
        <label className="grid gap-2 text-sm font-medium">
          Jurisdictions or periods of interest
          <input
            className={fieldClass}
            name="states_or_periods"
            placeholder="For example: Edo, Delta and Rivers; 2024–2026"
          />
        </label>
        <label className="grid gap-2 text-sm font-medium">
          Governed evidence domains requested
          <input
            className={fieldClass}
            name="requested_evidence_domains"
            placeholder="For example: FAAC, IGR, debt, budgets"
          />
        </label>
        <label className="grid gap-2 text-sm font-medium">
          Expected users
          <input
            className={fieldClass}
            name="expected_users"
            type="number"
            min={1}
            max={10000}
          />
        </label>
        <label className="grid gap-2 text-sm font-medium">
          Buying / evaluation timeline
          <select
            className={fieldClass}
            name="buying_timeline"
            defaultValue=""
          >
            <option value="">Not specified</option>
            <option value="immediate">Immediate / active decision</option>
            <option value="30_days">Within 30 days</option>
            <option value="this_quarter">This quarter</option>
            <option value="later">Later / exploratory</option>
          </select>
        </label>
      </div>

      <label className="grid gap-2 text-sm font-medium">
        Preferred delivery format
        <select
          className={fieldClass}
          name="preferred_format"
          defaultValue="xlsx"
        >
          <option value="xlsx">Excel workbook</option>
          <option value="pdf">PDF intelligence report</option>
          <option value="csv">CSV data</option>
          <option value="json">JSON data</option>
          <option value="api">API access</option>
          <option value="mixed">Multiple formats</option>
        </select>
      </label>

      <label className="hidden" aria-hidden="true">
        Website
        <input name="website" tabIndex={-1} autoComplete="off" />
      </label>

      <div className="flex flex-wrap items-center gap-4">
        <Button type="submit" disabled={status === 'submitting'}>
          {status === 'submitting' ? 'Submitting…' : 'Request pilot review'}
        </Button>
        <p className="text-muted-foreground text-sm">
          No payment is requested until coverage and deliverables are confirmed.
        </p>
      </div>

      {message ? (
        <p
          role="status"
          className={
            status === 'success'
              ? 'text-sm font-medium text-emerald-700 dark:text-emerald-400'
              : 'text-destructive text-sm font-medium'
          }
        >
          {message}
        </p>
      ) : null}
    </form>
  )
}
