'use client'

import { useState } from 'react'

import { Button } from '@/components/ui/button'

export function CopyHashButton({ value }: { value: string }) {
  const [copied, setCopied] = useState(false)

  async function copy() {
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
    } catch {
      setCopied(false)
    }
  }

  return (
    <span aria-live="polite">
      <Button type="button" variant="outline" size="sm" onClick={copy}>
        {copied ? 'Hash copied' : 'Copy hash'}
      </Button>
    </span>
  )
}
