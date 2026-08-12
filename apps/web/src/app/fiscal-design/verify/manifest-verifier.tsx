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

export function ManifestVerifier() {
  const [manifestText, setManifestText] = useState('')
  const [verification, setVerification] =
    useState<ManifestVerification | null>(null)
  const [isVerifying, setIsVerifying] = useState(false)

  async function verify() {
    setIsVerifying(true)
    try {
      setVerification(await verifyFiscalDesignEvidenceManifestText(manifestText))
    } finally {
      setIsVerifying(false)
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
