'use client'

import { useState } from 'react'

import { StatusPill } from '@/components/status-pill'
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
  coverage: 'Coverage',
  evidence: 'Evidence provenance',
  assumptions: 'Assumptions',
  scenario: 'Scenario outputs',
  objective: 'Research objective',
  other: 'Design version / other',
}

export function ManifestVerifier() {
  const [manifestText, setManifestText] = useState('')
  const [selectedManifestName, setSelectedManifestName] = useState<string | null>(
    null,
  )
  const [fileError, setFileError] = useState<string | null>(null)
  const [verification, setVerification] = useState<ManifestVerification | null>(
    null,
  )
  const [isVerifying, setIsVerifying] = useState(false)
  const [currentEvidence, setCurrentEvidence] =
    useState<CurrentEvidenceResult | null>(null)
  const [isCheckingCurrent, setIsCheckingCurrent] = useState(false)

  function resetVerificationState() {
    setVerification(null)
    setCurrentEvidence(null)
  }

  async function loadManifestFile(file: File | null) {
    if (!file) return

    setFileError(null)
    resetVerificationState()

    if (!file.name.toLowerCase().endsWith('.json')) {
      setSelectedManifestName(null)
      setFileError('Choose a .json Gaia Fiscal Design evidence manifest.')
      return
    }

    try {
      const text = await file.text()
      setManifestText(text)
      setSelectedManifestName(file.name)
    } catch {
      setSelectedManifestName(null)
      setFileError('The selected manifest could not be read in this browser.')
    }
  }

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
  const changeGroups = changeDetails.reduce<Record<string, string[]>>(
    (groups, change) => {
      groups[change.category] = [
        ...(groups[change.category] ?? []),
        change.detail,
      ]
      return groups
    },
    {},
  )
  const affectedCategoryCount = Object.keys(changeGroups).length

  return (
    <div className="mt-8 grid gap-6 lg:grid-cols-[1.3fr_0.7fr]">
      <Card>
        <CardHeader>
          <CardTitle>Load evidence manifest</CardTitle>
          <CardDescription>
            Choose a downloaded Gaia manifest or paste its JSON below.
            Verification stays in your browser until you explicitly run the
            optional current-evidence comparison.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg border border-dashed p-4">
            <label className="text-sm font-medium" htmlFor="manifest-file">
              Choose manifest file
            </label>
            <input
              id="manifest-file"
              type="file"
              accept="application/json,.json"
              className="border-input bg-background mt-2 block w-full rounded-md border px-3 py-2 text-sm"
              onChange={(event) => {
                void loadManifestFile(event.target.files?.[0] ?? null)
              }}
            />
            <p className="text-muted-foreground mt-2 text-xs leading-5">
              The file is read locally in your browser. Selecting it does not
              upload the manifest to Gaia.
            </p>
            {selectedManifestName ? (
              <p className="mt-3 text-sm font-medium">
                Loaded: {selectedManifestName}
              </p>
            ) : null}
            {fileError ? (
              <p className="mt-3 text-sm font-medium">{fileError}</p>
            ) : null}
          </div>

          <div className="my-5 flex items-center gap-3">
            <div className="border-border h-px flex-1 border-t" />
            <span className="text-muted-foreground text-xs font-medium uppercase">
              Or paste JSON
            </span>
            <div className="border-border h-px flex-1 border-t" />
          </div>

          <textarea
            value={manifestText}
            onChange={(event) => {
              setManifestText(event.target.value)
              setSelectedManifestName(null)
              setFileError(null)
              resetVerificationState()
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
              Load or paste a Gaia Fiscal Design evidence manifest and run
              verification.
            </p>
          ) : null}

          {verification?.status === 'verified' ? (
            <div>
              <div className="flex flex-wrap items-center gap-3">
                <StatusPill tone="success">Artifact intact</StatusPill>
                <p className="font-semibold">Verified manifest</p>
              </div>
              <p className="text-muted-foreground mt-2 text-sm leading-6">
                The embedded payload matches the manifest fingerprint.
              </p>
              <dl className="mt-5 grid gap-3 text-sm sm:grid-cols-3 lg:grid-cols-1">
                <div className="bg-muted/40 rounded-md border p-3">
                  <dt className="text-muted-foreground text-xs tracking-wide uppercase">
                    State
                  </dt>
                  <dd className="mt-1 font-medium">
                    {verification.stateName ?? 'Not supplied'}
                  </dd>
                </div>
                <div className="bg-muted/40 rounded-md border p-3">
                  <dt className="text-muted-foreground text-xs tracking-wide uppercase">
                    Year
                  </dt>
                  <dd className="mt-1 font-medium">
                    {verification.year ?? 'Not supplied'}
                  </dd>
                </div>
                <div className="bg-muted/40 rounded-md border p-3">
                  <dt className="text-muted-foreground text-xs tracking-wide uppercase">
                    Evidence records
                  </dt>
                  <dd className="mt-1 font-medium">
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
                    Change details are calculated locally against the loaded
                    manifest.
                  </p>
                </div>
              ) : null}

              {currentEvidence?.status === 'current' ? (
                <div className="mt-5 rounded-lg border border-emerald-200 bg-emerald-50/50 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="font-semibold">Current governed evidence</p>
                      <p className="text-muted-foreground mt-1 text-sm leading-6">
                        This artifact still matches Gaia&apos;s current governed
                        Fiscal Design response.
                      </p>
                    </div>
                    <StatusPill tone="success">Current</StatusPill>
                  </div>
                  <div className="mt-4 grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
                    <div className="bg-background/70 rounded-md border p-3">
                      <p className="text-muted-foreground text-xs tracking-wide uppercase">
                        Artifact integrity
                      </p>
                      <p className="mt-1 font-semibold">Verified</p>
                    </div>
                    <div className="bg-background/70 rounded-md border p-3">
                      <p className="text-muted-foreground text-xs tracking-wide uppercase">
                        Evidence freshness
                      </p>
                      <p className="mt-1 font-semibold">Current</p>
                    </div>
                    <div className="bg-background/70 rounded-md border p-3">
                      <p className="text-muted-foreground text-xs tracking-wide uppercase">
                        Detected changes
                      </p>
                      <p className="mt-1 font-semibold">0</p>
                    </div>
                  </div>
                  <p className="text-muted-foreground mt-4 text-xs leading-5">
                    {currentEvidence.state_name} · {currentEvidence.year} ·{' '}
                    {currentEvidence.coverage_label}
                  </p>
                </div>
              ) : null}

              {currentEvidence?.status === 'superseded' ? (
                <div className="mt-5 rounded-lg border border-amber-300 bg-amber-50/50 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="font-semibold">Superseded manifest</p>
                      <p className="text-muted-foreground mt-1 text-sm leading-6">
                        The artifact is internally intact, but Gaia&apos;s current
                        governed response now produces a different fingerprint.
                      </p>
                    </div>
                    <StatusPill tone="demo">Superseded</StatusPill>
                  </div>

                  <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
                    <div className="bg-background/70 rounded-md border p-3">
                      <p className="text-muted-foreground text-xs tracking-wide uppercase">
                        Artifact integrity
                      </p>
                      <p className="mt-1 font-semibold">Verified</p>
                    </div>
                    <div className="bg-background/70 rounded-md border p-3">
                      <p className="text-muted-foreground text-xs tracking-wide uppercase">
                        Evidence freshness
                      </p>
                      <p className="mt-1 font-semibold">Superseded</p>
                    </div>
                    <div className="bg-background/70 rounded-md border p-3">
                      <p className="text-muted-foreground text-xs tracking-wide uppercase">
                        Detected changes
                      </p>
                      <p className="mt-1 font-semibold">{changeDetails.length}</p>
                    </div>
                    <div className="bg-background/70 rounded-md border p-3">
                      <p className="text-muted-foreground text-xs tracking-wide uppercase">
                        Categories affected
                      </p>
                      <p className="mt-1 font-semibold">
                        {affectedCategoryCount}
                      </p>
                    </div>
                  </div>

                  <div className="mt-4 grid gap-3">
                    <div className="bg-background/70 rounded-md border p-3">
                      <p className="text-muted-foreground text-xs tracking-wide uppercase">
                        Manifest SHA-256
                      </p>
                      <p className="mt-1 font-mono text-xs break-all">
                        {currentEvidence.manifest_fingerprint}
                      </p>
                    </div>
                    <div className="bg-background/70 rounded-md border p-3">
                      <p className="text-muted-foreground text-xs tracking-wide uppercase">
                        Current SHA-256
                      </p>
                      <p className="mt-1 font-mono text-xs break-all">
                        {currentEvidence.current_fingerprint}
                      </p>
                    </div>
                  </div>

                  <div className="mt-5 border-t border-amber-200 pt-5">
                    <div className="flex flex-wrap items-end justify-between gap-2">
                      <div>
                        <p className="text-sm font-semibold">What changed</p>
                        <p className="text-muted-foreground mt-1 text-xs leading-5">
                          Differences are grouped by governed dimension so you can
                          see why the fingerprint moved.
                        </p>
                      </div>
                      {changeDetails.length ? (
                        <span className="text-muted-foreground text-xs">
                          {changeDetails.length} change
                          {changeDetails.length === 1 ? '' : 's'}
                        </span>
                      ) : null}
                    </div>
                    {changeDetails.length ? (
                      <div className="mt-4 space-y-3">
                        {Object.entries(changeGroups).map(
                          ([category, details]) => (
                            <div
                              key={category}
                              className="bg-background/80 rounded-md border p-3"
                            >
                              <div className="flex items-center justify-between gap-3">
                                <p className="text-sm font-semibold">
                                  {changeCategoryLabels[category] ?? category}
                                </p>
                                <span className="bg-muted rounded-full px-2 py-1 text-xs font-medium">
                                  {details.length}
                                </span>
                              </div>
                              <ul className="text-muted-foreground mt-2 space-y-2 text-sm leading-6">
                                {details.map((detail, index) => (
                                  <li key={`${category}-${index}`}>• {detail}</li>
                                ))}
                              </ul>
                            </div>
                          ),
                        )}
                      </div>
                    ) : (
                      <p className="text-muted-foreground mt-3 text-sm leading-6">
                        The canonical payload changed, but no supported
                        difference category was detected.
                      </p>
                    )}
                  </div>
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
              <StatusPill tone="demo">Integrity failed</StatusPill>
              <p className="mt-3 font-semibold">Fingerprint mismatch</p>
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
              <StatusPill>Invalid artifact</StatusPill>
              <p className="mt-3 font-semibold">Invalid manifest</p>
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
