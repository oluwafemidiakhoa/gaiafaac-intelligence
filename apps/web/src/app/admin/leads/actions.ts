'use server'

import { revalidatePath } from 'next/cache'

import { updatePilotLead } from '@/lib/commercial-api'

const ALLOWED_STATUSES = new Set([
  'new',
  'contacted',
  'qualified',
  'pilot',
  'proposal',
  'won',
  'lost',
])

export async function updateLeadAction(formData: FormData) {
  const leadId = String(formData.get('lead_id') ?? '')
  const status = String(formData.get('status') ?? '')
  if (!leadId || !ALLOWED_STATUSES.has(status)) return

  const ownerName = String(formData.get('owner_name') ?? '').trim()
  const nextAction = String(formData.get('next_action') ?? '').trim()
  const nextActionAt = String(formData.get('next_action_at') ?? '').trim()
  const closedReason = String(formData.get('closed_reason') ?? '').trim()

  await updatePilotLead(leadId, {
    status,
    owner_name: ownerName || null,
    next_action: nextAction || null,
    next_action_at: nextActionAt ? new Date(nextActionAt).toISOString() : null,
    closed_reason: closedReason || null,
  })
  revalidatePath('/admin/leads')
}
