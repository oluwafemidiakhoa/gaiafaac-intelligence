import { NextResponse } from 'next/server'
import { z } from 'zod'

const requestSchema = z.object({
  name: z.string().trim().min(2).max(200),
  email: z.string().trim().email().max(320),
  organization: z.string().trim().max(200).optional().default(''),
  role: z.string().trim().max(160).optional().default(''),
  country: z.string().trim().max(120).optional().default(''),
  plan_interest: z.enum(['analyst', 'team', 'api']),
  use_case: z.string().trim().min(20).max(4000),
  states_or_periods: z.string().trim().max(2000).optional().default(''),
  requested_evidence_domains: z
    .string()
    .trim()
    .max(2000)
    .optional()
    .default(''),
  preferred_format: z.string().trim().max(80).optional().default(''),
  expected_users: z.number().int().min(1).max(10000).nullable().optional(),
  buying_timeline: z.string().trim().max(240).optional().default(''),
  source_page: z.string().trim().max(500).optional().default('/pilot'),
  website: z.string().trim().max(200).optional().default(''),
})

function apiBaseUrl() {
  return z
    .url()
    .parse(
      process.env.API_INTERNAL_URL ??
        process.env.NEXT_PUBLIC_API_URL ??
        'http://localhost:8000',
    )
    .replace(/\/$/, '')
}

export async function POST(request: Request) {
  let input: unknown
  try {
    input = await request.json()
  } catch {
    return NextResponse.json(
      { error: 'Invalid request body.' },
      { status: 400 },
    )
  }

  const parsed = requestSchema.safeParse(input)
  if (!parsed.success) {
    return NextResponse.json(
      { error: 'Please review the highlighted fields and try again.' },
      { status: 422 },
    )
  }

  try {
    const response = await fetch(
      `${apiBaseUrl()}/api/v1/commercial/pilot-leads`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(parsed.data),
        cache: 'no-store',
      },
    )

    if (!response.ok) {
      return NextResponse.json(
        { error: 'The pilot request service is temporarily unavailable.' },
        { status: 502 },
      )
    }

    return NextResponse.json(await response.json(), { status: 202 })
  } catch {
    return NextResponse.json(
      { error: 'The pilot request service is temporarily unavailable.' },
      { status: 502 },
    )
  }
}
