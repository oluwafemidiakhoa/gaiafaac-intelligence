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
    }
  | { status: 'error'; message: string }

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
            This checks artifact integrity only. It does not independently
            validate the underlying government source documents.
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
              <p className="font-semibold">Verified manifest</p>
              <p className="text-muted-foreground mt-2 text-sm leading-6">
                The embedded payload matches the manifest fingerprint.
              </p>
              <dl className="mt-5 space-y-3 text-sm">
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
              <p className="text-muted-foreground mt-5 font-mono text-xs break-all">
                SHA-256 {verification.fingerprint}
              </p>

              {verification.currentEvidenceCheck ? (
                <div className="mt-5 border-t pt-5">
                  <Button
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
                    This optional check sends only the scenario identifiers and
                    fingerprint needed to recompute the current governed brief.
                  </p>
                </div>
              ) : null}

              {currentEvidence?.status === 'current' ? (
                <div className="mt-5 rounded-md border p-4">
                  <p className="font-semibold">Current governed evidence</p>
                  <p className="text-muted-foreground mt-2 text-sm leading-6">
                    This manifest fingerprint still matches Gaia&apos;s current
                    governed Fiscal Design response for this scenario.
                  </p>
                  <p className="text-muted-foreground mt-2 text-xs">
                    {currentEvidence.coverage_label}
                  </p>
                </div>
              ) : null}

              {currentEvidence?.status === 'superseded' ? (
                <div className="mt-5 rounded-md border p-4">
                  <p className="font-semibold">Superseded manifest</p>
                  <p className="text-muted-foreground mt-2 text-sm leading-6">
                    The artifact is internally intact, but Gaia&apos;s current
                    governed response now produces a different fingerprint.
                  </p>
                  <p className="text-muted-foreground mt-3 font-mono text-xs break-all">
                    Current SHA-256 {currentEvidence.current_fingerprint}
                  </p>
                </div>
              ) : null}

              {currentEvidence?.status === 'error' ? (
                <div className="mt-5 rounded-md border p-4">
                  <p className="font-semibold">Current evidence unavailable</p>
                  <p className="text-muted-foreground mt-2 text-sm leading-6">
                    {currentEvidence.message}
                  </p>
                </div>
              ) : null}
            </div>
          ) : null}

          {verification?.status === 'mismatch' ? (
            <div>
              <p className="font-semibold">Fingerprint mismatch</p>
              <p className="text-muted-foreground mt-2 text-sm leading-6">
                The payload does not match the fingerprint embedded in this
                manifest. Treat the artifact as changed or corrupted.
              </p>
              <p className="text-muted-foreground mt-4 font-mono text-xs break-all">
                Embedded: {verification.fingerprint}
              </p>
              <p className="text-muted-foreground mt-2 font-mono text-xs break-all">
                Computed: {verification.computedFingerprint}
              </p>
            </div>
          ) : null}

          {verification?.status === 'invalid' ? (
            <div>
              <p className="font-semibold">Invalid manifest</p>
              <p className="text-muted-foreground mt-2 text-sm leading-6">
                {verification.message}
              </p>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  )
}
