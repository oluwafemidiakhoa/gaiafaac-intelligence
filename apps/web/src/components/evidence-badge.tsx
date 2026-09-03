'use client'

import React from 'react'
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  FileText,
  Hash,
  AlertTriangle,
} from 'lucide-react'
import {
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

export type EvidenceStatus =
  | 'published'
  | 'draft'
  | 'demo'
  | 'conflicted'
  | 'pending'

interface EvidenceSource {
  organization: string
  url?: string
  documentVersion?: string
  pageNumber?: string
  sha256?: string
}

interface EvidenceBadgeProps {
  status: EvidenceStatus
  source?: EvidenceSource
  revisedAt?: Date
  publishedAt?: Date
  reviewedBy?: string
  approvedBy?: string
  conflictCount?: number
  className?: string
}

const statusConfig = {
  published: {
    color: 'bg-green-100 text-green-800',
    icon: CheckCircle2,
    label: 'Published',
    description: 'Verified and officially published',
  },
  draft: {
    color: 'bg-blue-100 text-blue-800',
    icon: Clock,
    label: 'Draft',
    description: 'Under review, not yet published',
  },
  demo: {
    color: 'bg-amber-100 text-amber-800',
    icon: AlertTriangle,
    label: 'Demo',
    description: 'Demo data for testing only',
  },
  conflicted: {
    color: 'bg-red-100 text-red-800',
    icon: AlertCircle,
    label: 'Conflicted',
    description: 'Multiple conflicting sources detected',
  },
  pending: {
    color: 'bg-gray-100 text-gray-800',
    icon: Clock,
    label: 'Pending',
    description: 'Awaiting verification',
  },
}

export function EvidenceBadge({
  status,
  source,
  revisedAt,
  publishedAt,
  reviewedBy,
  approvedBy,
  conflictCount,
  className = '',
}: EvidenceBadgeProps) {
  const config = statusConfig[status]
  const Icon = config.icon

  const tooltipContent = (
    <div className="space-y-2 text-xs">
      <div className="font-semibold">{config.description}</div>

      {source && (
        <div className="border-t border-gray-300 pt-2">
          <div className="font-semibold">Source</div>
          <div className="text-gray-300">{source.organization}</div>
          {source.documentVersion && (
            <div className="text-gray-400">v{source.documentVersion}</div>
          )}
          {source.pageNumber && (
            <div className="text-gray-400">p. {source.pageNumber}</div>
          )}
          {source.url && (
            <a
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="break-all text-blue-300 hover:underline"
            >
              {source.url.substring(0, 50)}...
            </a>
          )}
        </div>
      )}

      {source?.sha256 && (
        <div className="border-t border-gray-300 pt-2">
          <div className="flex items-center gap-1 font-semibold">
            <Hash className="h-3 w-3" />
            Document Hash (SHA-256)
          </div>
          <div className="font-mono break-all text-gray-400">
            {source.sha256.substring(0, 16)}...
          </div>
        </div>
      )}

      {reviewedBy && (
        <div className="border-t border-gray-300 pt-2">
          <div className="text-gray-400">Reviewed by: {reviewedBy}</div>
        </div>
      )}

      {approvedBy && (
        <div className="text-gray-400">Approved by: {approvedBy}</div>
      )}

      {publishedAt && (
        <div className="text-gray-400">
          Published: {publishedAt.toLocaleDateString()}
        </div>
      )}

      {revisedAt && (
        <div className="text-gray-400">
          Last revised: {revisedAt.toLocaleDateString()}
        </div>
      )}

      {conflictCount && conflictCount > 0 && (
        <div className="border-t border-red-300 pt-2">
          <div className="text-red-300">
            ⚠️ {conflictCount} conflicting source(s) detected
          </div>
        </div>
      )}
    </div>
  )

  return (
    <TooltipProvider>
      <div className="relative inline-flex">
        <TooltipTrigger asChild>
          <div
            className={`inline-flex cursor-help items-center gap-1 rounded px-2 py-1 text-xs font-medium ${config.color} ${className}`}
          >
            <Icon className="h-3 w-3" />
            {config.label}
          </div>
        </TooltipTrigger>
        <TooltipContent className="max-w-xs border-slate-700 bg-slate-900 text-white">
          {tooltipContent}
        </TooltipContent>
      </div>
    </TooltipProvider>
  )
}

/**
 * Display evidence badge inline with a fiscal number
 * Usage: <FiscalNumberWithEvidence amount={50000} currency="₦" evidence={...} />
 */
interface FiscalNumberWithEvidenceProps {
  amount: number
  currency?: string
  evidence: EvidenceBadgeProps
  className?: string
}

export function FiscalNumberWithEvidence({
  amount,
  currency = '₦',
  evidence,
  className = '',
}: FiscalNumberWithEvidenceProps) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <span className="text-lg font-semibold">
        {currency}
        {amount.toLocaleString('en-NG', { minimumFractionDigits: 2 })}
      </span>
      <EvidenceBadge {...evidence} />
    </div>
  )
}

/**
 * Show evidence trail for a data point
 */
interface EvidenceTrailProps {
  sourceOrganization: string
  documentUrl?: string
  sha256?: string
  verificationStatus: EvidenceStatus
  publishedAt?: Date
  revisions?: Array<{
    date: Date
    changeDescription: string
    revisedBy: string
  }>
}

export function EvidenceTrail({
  sourceOrganization,
  documentUrl,
  sha256,
  verificationStatus,
  publishedAt,
  revisions = [],
}: EvidenceTrailProps) {
  return (
    <div className="space-y-3 rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm">
      <div className="flex items-start justify-between">
        <div>
          <h4 className="font-semibold text-slate-900">Evidence Trail</h4>
          <p className="text-slate-600">Source and verification history</p>
        </div>
        <EvidenceBadge status={verificationStatus} />
      </div>

      <div className="space-y-2 rounded bg-white p-3">
        <div className="flex items-start gap-2">
          <FileText className="mt-0.5 h-4 w-4 flex-shrink-0 text-slate-400" />
          <div>
            <div className="font-medium text-slate-900">
              {sourceOrganization}
            </div>
            {documentUrl && (
              <a
                href={documentUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs break-all text-blue-600 hover:underline"
              >
                View source document
              </a>
            )}
          </div>
        </div>

        {sha256 && (
          <div className="flex items-start gap-2 pt-2">
            <Hash className="mt-0.5 h-4 w-4 flex-shrink-0 text-slate-400" />
            <div>
              <div className="text-xs font-medium text-slate-900">SHA-256</div>
              <div className="font-mono text-xs break-all text-slate-600">
                {sha256}
              </div>
            </div>
          </div>
        )}
      </div>

      {publishedAt && (
        <div className="text-xs text-slate-600">
          Published: {publishedAt.toLocaleDateString()} at{' '}
          {publishedAt.toLocaleTimeString()}
        </div>
      )}

      {revisions.length > 0 && (
        <div className="border-t border-slate-200 pt-2">
          <h5 className="mb-2 text-xs font-semibold text-slate-900">
            Revision History
          </h5>
          <div className="space-y-2">
            {revisions.map((rev, idx) => (
              <div
                key={idx}
                className="rounded border border-slate-200 bg-white p-2 text-xs"
              >
                <div className="font-medium text-slate-900">
                  {rev.date.toLocaleDateString()}
                </div>
                <div className="text-slate-600">{rev.changeDescription}</div>
                <div className="text-xs text-slate-500">by {rev.revisedBy}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
