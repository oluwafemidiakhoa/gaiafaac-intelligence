'use client'

import React, { useEffect, useState } from 'react'
import { AlertCircle, FileText, Lock, RotateCw } from 'lucide-react'
import { EvidenceBadge } from './evidence-badge'
import { Button } from './ui/button'

interface FiscalDataPoint {
  gaiaId: string
  value: number
  currency: string
  label: string
  period: string
  jurisdiction: string
  description?: string
}

interface ProvenanceData {
  gaiaId: string
  claimValue: string
  claimCurrency: string
  claimType: string
  jurisdiction: string
  period: string
  verificationStatus: 'published' | 'draft' | 'demo' | 'conflicted' | 'pending'
  source: {
    organization: string
    url?: string
    documentVersion?: string
    pageNumber?: string
    sha256?: string
  }
  review: {
    reviewedAt?: string
    reviewedBy?: string
    approvedAt?: string
    approvedBy?: string
    reviewNotes?: string
  }
  publishedAt?: string
  createdAt: string
  revisions: Array<{
    date: string
    changeDescription: string
    revisedBy: string
    sourceRevision: boolean
  }>
  conflictCount: number
  conflictingClaims: string[]
}

interface FiscalDataWithEvidenceProps {
  data: FiscalDataPoint
  showDetails?: boolean
  onViewConflicts?: (gaiaId: string) => void
}

export function FiscalDataWithEvidence({
  data,
  showDetails = false,
  onViewConflicts,
}: FiscalDataWithEvidenceProps) {
  const [provenance, setProvenance] = useState<ProvenanceData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState(showDetails)

  useEffect(() => {
    const fetchProvenance = async () => {
      try {
        setLoading(true)
        const response = await fetch(
          `/api/v1/evidence/provenance/${data.gaiaId}`,
        )
        if (!response.ok) throw new Error('Failed to fetch provenance')
        const result = await response.json()
        setProvenance(result)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    fetchProvenance()
  }, [data.gaiaId])

  if (loading) {
    return (
      <div className="animate-pulse rounded-lg border border-slate-200 bg-slate-50 p-4">
        <div className="mb-2 h-8 w-32 rounded bg-slate-200" />
        <div className="h-4 w-48 rounded bg-slate-200" />
      </div>
    )
  }

  if (error || !provenance) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
        <div className="flex items-center gap-2">
          <AlertCircle className="h-4 w-4" />
          <span>Could not load evidence for this data point</span>
        </div>
      </div>
    )
  }

  const conflictedStatus =
    provenance.verificationStatus === 'conflicted'
      ? 'conflicted'
      : provenance.verificationStatus === 'demo'
        ? 'demo'
        : provenance.verificationStatus === 'draft'
          ? 'draft'
          : 'published'

  return (
    <div className="space-y-3">
      {/* Main Data Display */}
      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <div className="mb-3 flex items-start justify-between">
          <div>
            <h3 className="font-semibold text-slate-900">{data.label}</h3>
            <p className="text-sm text-slate-600">{data.description}</p>
          </div>
          <EvidenceBadge
            status={conflictedStatus}
            source={{
              organization: provenance.source.organization,
              url: provenance.source.url,
              documentVersion: provenance.source.documentVersion,
              pageNumber: provenance.source.pageNumber,
              sha256: provenance.source.sha256,
            }}
            reviewedBy={provenance.review.reviewedBy}
            approvedBy={provenance.review.approvedBy}
            publishedAt={
              provenance.publishedAt
                ? new Date(provenance.publishedAt)
                : undefined
            }
            conflictCount={provenance.conflictCount}
          />
        </div>

        <div className="mb-3 rounded bg-slate-50 p-3">
          <div className="text-2xl font-bold text-slate-900">
            {provenance.claimCurrency}
            {parseFloat(provenance.claimValue).toLocaleString('en-NG', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </div>
          <div className="mt-1 text-xs text-slate-600">
            {provenance.jurisdiction} • {provenance.period}
          </div>
        </div>

        {/* Source Organization */}
        <div className="flex items-start gap-2 rounded border border-blue-100 bg-blue-50 p-3 text-sm">
          <FileText className="mt-0.5 h-4 w-4 flex-shrink-0 text-blue-600" />
          <div className="flex-1">
            <div className="font-medium text-blue-900">
              {provenance.source.organization}
            </div>
            {provenance.source.url && (
              <a
                href={provenance.source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-blue-600 hover:underline"
              >
                View source document →
              </a>
            )}
          </div>
        </div>

        {/* Document Hash */}
        {provenance.source.sha256 && (
          <div className="mt-3 rounded border border-slate-200 bg-slate-50 p-3 text-xs">
            <div className="mb-1 flex items-center gap-2">
              <Lock className="h-3 w-3 text-slate-500" />
              <span className="font-semibold text-slate-700">
                Document Fingerprint
              </span>
            </div>
            <div className="font-mono break-all text-slate-600">
              {provenance.source.sha256}
            </div>
            <p className="mt-1 text-slate-500">
              SHA-256 hash ensures document integrity and authenticity
            </p>
          </div>
        )}

        {/* Review Status */}
        {provenance.review.reviewedBy || provenance.review.approvedBy ? (
          <div className="mt-3 space-y-1 rounded border border-green-200 bg-green-50 p-3 text-xs">
            {provenance.review.reviewedBy && (
              <div>
                <span className="font-semibold text-green-900">
                  Reviewed by:
                </span>
                <span className="text-green-800">
                  {' '}
                  {provenance.review.reviewedBy}
                </span>
                {provenance.review.reviewedAt && (
                  <span className="text-green-700">
                    {' '}
                    (
                    {new Date(
                      provenance.review.reviewedAt,
                    ).toLocaleDateString()}
                    )
                  </span>
                )}
              </div>
            )}
            {provenance.review.approvedBy && (
              <div>
                <span className="font-semibold text-green-900">
                  Approved by:
                </span>
                <span className="text-green-800">
                  {' '}
                  {provenance.review.approvedBy}
                </span>
                {provenance.review.approvedAt && (
                  <span className="text-green-700">
                    {' '}
                    (
                    {new Date(
                      provenance.review.approvedAt,
                    ).toLocaleDateString()}
                    )
                  </span>
                )}
              </div>
            )}
            <p className="pt-1 text-green-700 italic">
              ✓ Four-eyes verification complete (separate review & approval)
            </p>
          </div>
        ) : (
          <div className="mt-3 rounded border border-amber-200 bg-amber-50 p-3 text-xs">
            <span className="text-amber-900">⚠️ Awaiting verification</span>
          </div>
        )}

        {/* Conflicts */}
        {provenance.conflictCount > 0 && (
          <div className="mt-3 rounded border border-red-200 bg-red-50 p-3 text-xs">
            <div className="flex items-start justify-between">
              <div>
                <div className="mb-1 font-semibold text-red-900">
                  ⚠️ {provenance.conflictCount} conflicting source(s) detected
                </div>
                <p className="text-red-800">
                  Multiple authoritative sources report different values for
                  this period. Review all sources before making decisions.
                </p>
              </div>
              {onViewConflicts && (
                <Button
                  onClick={() => onViewConflicts(data.gaiaId)}
                  variant="outline"
                  size="sm"
                  className="ml-2 flex-shrink-0"
                >
                  Review
                </Button>
              )}
            </div>
          </div>
        )}

        {/* Expand Details */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-3 flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900"
        >
          <RotateCw className="h-4 w-4" />
          {expanded ? 'Hide' : 'Show'} revision history & details
        </button>
      </div>

      {/* Expanded Details */}
      {expanded && provenance.revisions.length > 0 && (
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
          <h4 className="mb-3 font-semibold text-slate-900">
            Revision History
          </h4>
          <div className="space-y-2">
            {provenance.revisions.map((rev, idx) => (
              <div
                key={idx}
                className="rounded border border-slate-200 bg-white p-3 text-sm"
              >
                <div className="mb-1 flex items-start justify-between">
                  <div className="font-medium text-slate-900">
                    {new Date(rev.date).toLocaleDateString()}
                  </div>
                  {rev.sourceRevision && (
                    <span className="rounded bg-orange-100 px-2 py-1 text-xs text-orange-800">
                      Source changed
                    </span>
                  )}
                </div>
                <p className="text-slate-700">{rev.changeDescription}</p>
                <p className="mt-1 text-xs text-slate-500">
                  by {rev.revisedBy}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

/**
 * Display multiple fiscal data points with a unified evidence view
 * Used on institutional dashboards to show complete evidence for key metrics
 */
interface FiscalDataGridProps {
  title: string
  description?: string
  data: FiscalDataPoint[]
  columns?: number
}

export function FiscalDataGrid({
  title,
  description,
  data,
  columns = 2,
}: FiscalDataGridProps) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">{title}</h2>
        {description && <p className="mt-1 text-slate-600">{description}</p>}
      </div>

      <div
        className={`grid gap-4`}
        style={{
          gridTemplateColumns: `repeat(auto-fit, minmax(${columns === 1 ? '100%' : '300px'}, 1fr))`,
        }}
      >
        {data.map((point) => (
          <FiscalDataWithEvidence key={point.gaiaId} data={point} />
        ))}
      </div>
    </div>
  )
}
