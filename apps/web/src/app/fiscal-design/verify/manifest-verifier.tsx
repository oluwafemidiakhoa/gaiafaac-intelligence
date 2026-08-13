'use client'

import { useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  type ManifestVerification,
  summarizeFiscalDesignPayloadChanges,
  verifyFiscalDesignEvidenceManifestText,
} from '@/lib/fiscal-design-manifest-verifier'

type CurrentEvidenceResult =
  | {
      status: 'current' | 'superseded'
      manifest_fingerprint: string
      current_fingerprint: string
      state_name: string
      year: number
      coverage_label: string
      current_payload: Record<string, unknown>
    }
  | { status: 'error'; message: string }

const changeCategoryLabels: Record<string, string> = {
  evidence: 'Evidence',
  coverage: 'Coverage',
  assumptions: 'Assumptions',
  scenario: 'Scenario outputs',
  objective: 'Objective',
  version: 'Design version',
}

export function ManifestVerifier() {
  const [manifestText, setManifestText] = useState('')
  const [verification, setVerification] = useState<ManifestVerification | null>(
    null,
  )
  const [isVerifying, setIsVerifying] = useState(false)
  const [currentEvidence, setCurrentEvidence] =
    useState<CurrentEvidenceResult | null>(null)
  const [isCheckingCurrent, setIsCheckingCurrent] = useState(false)

  async function verify() {
    setIsVerifying(true)
    setCurrentEvidence(null)
    try {
      setVerification(
        await verifyFiscalDesignEvidenceManifestText(manifestText),
      )
    } finally {
      setIsVerifying(false)
    }
  }

  async function checkCurrentEvidence() {
    if (
      verification?.status !== 'verified' ||
      !verification.currentEvidenceCheck
    ) {
      return
    }

    setIsCheckingCurrent(true)
    setCurrentEvidence(null)
    try {
      const response = await fetch('/fiscal-design/verify/current', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(verification.currentEvidenceCheck),
      })
      const body = (await response.json()) as Record<string, unknown>
      if (!response.ok) {
        setCurrentEvidence({
          status: 'error',
          message:
            typeof body.error === 'string'
              ? body.error
              : 'Current governed evidence could not be checked.',
        })
        return
      }

      setCurrentEvidence(body as CurrentEvidenceResult)
    } catch {
      setCurrentEvidence({
        status: 'error',
        message: 'Current governed evidence could not be checked.',
      })
    } finally {
      setIsCheckingCurrent(false)
    }
  }

  const changeDetails =
    verification?.status === 'verified' &&
    currentEvidence?.status === 'superseded'
      ? summarizeFiscalDesignPayloadChanges(
          verification.payload,
          currentEvidence.current_payload,
        )
      : []
  const changedCategories = Array.from(
    new Set(changeDetails.map((change) => change.category)),
  )

  return (
    <div className="mt-8 grid gap-6 lg:grid-cols-[1.3fr_0.7fr]">
      <Card>
        <CardHeader>
          <CardTitle>Paste evidence manifest</CardTitle>
          <CardDescription>
            Verification happens in your browser. Gaia recomputes SHA-256 over
            the embedded canonical payload and compares it with the manifest
            fingerprint.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <textarea
            value={manifestText}
            onChange={(event) => {
              setManifestText(event.target.value)
              setVerification(null)
              setCurrentEvidence(null)
            }}
            placeholder='{"manifest_version":"gaia-fiscal-design-evidence-manifest-v1",...}'
            className="border-input bg-background min-h-80 w-full rounded-md border p-3 font-mono text-xs leading-5"
            spellCheck={false}
          />
          <div className="mt-4">
            <Button
              type="button"
              onClick={verify}
              disabled={!manifestText.trim() || isVerifying}
            >
              {isVerifying ? 'Verifying…' : 'Verify manifest'}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Verification result</CardTitle>
          <CardDescription>
            First verify artifact integrity, then optionally compare the verified
            artifact with Gaia&apos;s current governed evidence.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!verification ? (
            <p className="text-muted-foreground text-sm leading-6">
              Paste a Gaia Fiscal Design evidence manifest and run verification.
            </p>
          ) : null}

          {verification?.status === 'verified' ? (
            <div>
              <div className="rounded-lg border p-4">
                <p className="text-xs font-semibold tracking-wide uppercase">
                  Step 1 · Artifact integrity
                </p>
                <p className="mt-2 text-lg font-semibold">Verified manifest</p>
                <p className="text-muted-foreground mt-1 text-sm leading-6">
                  The embedded payload matches the manifest fingerprint. This
                  proves the artifact is internally intact; it does not prove the
                  underlying source documents are correct.
                </p>
                <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
                  <div>
                    <dt className="text-muted-foreground">State</dt>
                    <dd className="font-medium">
                      {verification.stateName ?? 'Not supplied'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Year</dt>
                    <dd className="font-medium">
                      {verification.year ?? 'Not supplied'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Evidence records</dt>
                    <dd className="font-medium">
                      {verification.evidenceCount ?? 'Not supplied'}
                    </dd>
                  </div>
                </dl>
                <p className="text-muted-foreground mt-4 font-mono text-xs break-all">
                  Manifest SHA-256 {verification.fingerprint}
                </p>
              </div>

              {verification.currentEvidenceCheck ? (
                <div className="mt-5 rounded-lg border border-dashed p-4">
                  <p className="text-xs font-semibold tracking-wide uppercase">
                    Step 2 · Evidence currency
                  </p>
                  <p className="mt-2 font-semibold">
                    Is this artifact still current?
                  </p>
                  <p className="text-muted-foreground mt-1 text-sm leading-6">
                    Compare this verified artifact with Gaia&apos;s current governed
                    response for the same scenario.
                  </p>
                  <Button
                    className="mt-4"
                    type="button"
                    variant="outline"
                    onClick={checkCurrentEvidence}
                    disabled={isCheckingCurrent}
                  >
                    {isCheckingCurrent
                      ? 'Checking current evidence…'
                      : 'Check against current evidence'}
                  </Button>
                  <p className="text-muted-foreground mt-2 text-xs leading-5">
                    Only the scenario identifiers and fingerprint needed for
                    recomputation are sent. Change details are calculated locally
                    against the pasted manifest.
                  </p>
                </div>
              ) : null}

              {currentEvidence?.status === 'current' ? (
                <div className="mt-5 rounded-lg border p-4">
                  <p className="text-xs font-semibold tracking-wide uppercase">
                    Current · No evidence drift detected
                  </p>
                  <p className="mt-2 text-lg font-semibold">
                    Current governed evidence
                  </p>
                  <p className="text-muted-foreground mt-1 text-sm leading-6">
                    The manifest fingerprint still matches Gaia&apos;s current
                    governed Fiscal Design response for this scenario. No
                    supported evidence or scenario change is detected.
                  </p>
                  <p className="mt-4 text-sm font-medium">
                    Recommended action: this artifact can continue to be used as
                    the current verified brief.
                  </p>
                  <p className="text-muted-foreground mt-3 text-xs">
                    Coverage: {currentEvidence.coverage_label}
                  </p>
                </div>
              ) : null}

              {currentEvidence?.status === 'superseded' ? (
                <div className="mt-5 rounded-lg border p-4">
                  <p className="text-xs font-semibold tracking-wide uppercase">
                    Superseded · Evidence drift detected
                  </p>
                  <p className="mt-2 text-lg font-semibold">
                    Review before relying on this artifact
                  </p>
                  <p className="text-muted-foreground mt-1 text-sm leading-6">
                    The artifact is internally intact, but Gaia&apos;s current
                    governed response now produces a different fingerprint.
                  </p>

                  {changedCategories.length ? (
                    <div className="mt-4 flex flex-wrap gap-2">
                      {changedCategories.map((category) => (
                        <span
                          key={category}
                          className="bg-muted rounded-full px-3 py-1 text-xs font-medium"
                        >
                          {changeCategoryLabels[category] ?? category}
                        </span>
                      ))}
                    </div>
                  ) : null}

                  <div className="mt-5 grid gap-3 text-xs sm:grid-cols-2">
                    <div className="rounded-md border p-3">
                      <p className="text-muted-foreground font-medium">
                        Manifest fingerprint
                      </p>
                      <p className="mt-2 font-mono break-all">
                        {currentEvidence.manifest_fingerprint}
                      </p>
                    </div>
                    <div className="rounded-md border p-3">
                      <p className="text-muted-foreground font-medium">
                        Current fingerprint
                      </p>
                      <p className="mt-2 font-mono break-all">
                        {currentEvidence.current_fingerprint}
                      </p>
                    </div>
                  </div>

                  <div className="mt-5 border-t pt-4">
                    <div className="flex flex-wrap items-baseline justify-between gap-2">
                      <p className="text-sm font-semibold">What changed</p>
                      <p className="text-muted-foreground text-xs">
                        {changeDetails.length} detected change
                        {changeDetails.length === 1 ? '' : 's'}
                      </p>
                    </div>
                    {changeDetails.length ? (
                      <div className="mt-3 space-y-3">
                        {changeDetails.map((change, index) => (
                          <div
                            key={`${change.category}-${index}`}
                            className="rounded-md border p-3"
                          >
                            <p className="text-xs font-semibold tracking-wide uppercase">
                              {changeCategoryLabels[change.category] ??
                                change.category}
                            </p>
                            <p className="text-muted-foreground mt-1 text-sm leading-6">
                              {change.detail}
                            </p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-muted-foreground mt-2 text-sm leading-6">
                        The canonical payload changed, but no supported
                        difference category was detected.
                      </p>
                    )}
                  </div>

                  <p className="mt-5 text-sm font-medium">
                    Recommended action: regenerate the Fiscal Design brief before
                    using it for a new decision, publication, or review.
                  </p>
                </div>
              ) : null}

              {currentEvidence?.status === 'error' ? (
                <div className="mt-5 rounded-lg border p-4">
                  <p className="text-xs font-semibold tracking-wide uppercase">
                    Current status unavailable
                  </p>
                  <p className="mt-2 font-semibold">
                    Current evidence could not be checked
                  </p>
                  <p className="text-muted-foreground mt-1 text-sm leading-6">
                    {currentEvidence.message}
                  </p>
                  <p className="text-muted-foreground mt-3 text-xs leading-5">
                    The local artifact-integrity result above remains valid. This
                    error only means Gaia could not determine whether newer
                    governed evidence has superseded it.
                  </p>
                </div>
              ) : null}
            </div>
          ) : null}

          {verification?.status === 'mismatch' ? (
            <div className="rounded-lg border p-4">
              <p className="text-xs font-semibold tracking-wide uppercase">
                Failed · Artifact integrity
              </p>
              <p className="mt-2 text-lg font-semibold">Fingerprint mismatch</p>
              <p className="text-muted-foreground mt-1 text-sm leading-6">
                The payload does not match the fingerprint embedded in this
                manifest. Treat the artifact as changed or corrupted and do not
                use it as a verified brief.
              </p>
              <div className="mt-4 space-y-3 text-xs">
                <div className="rounded-md border p-3">
                  <p className="text-muted-foreground font-medium">Embedded</p>
                  <p className="mt-2 font-mono break-all">
                    {verification.fingerprint}
                  </p>
                </div>
                <div className="rounded-md border p-3">
                  <p className="text-muted-foreground font-medium">Computed</p>
                  <p className="mt-2 font-mono break-all">
                    {verification.computedFingerprint}
                  </p>
                </div>
              </div>
            </div>
          ) : null}

          {verification?.status === 'invalid' ? (
            <div className="rounded-lg border p-4">
              <p className="text-xs font-semibold tracking-wide uppercase">
                Failed · Manifest structure
              </p>
              <p className="mt-2 text-lg font-semibold">Invalid manifest</p>
              <p className="text-muted-foreground mt-1 text-sm leading-6">
                {verification.message}
              </p>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  )
}
