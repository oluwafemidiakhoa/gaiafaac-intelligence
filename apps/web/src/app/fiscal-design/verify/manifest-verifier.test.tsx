import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { ManifestVerifier } from './manifest-verifier'

describe('ManifestVerifier', () => {
  it('loads a selected JSON manifest into the verifier', async () => {
    render(<ManifestVerifier />)
    const manifestText = JSON.stringify({
      manifest_version: 'gaia-fiscal-design-evidence-manifest-v1',
      fingerprint_algorithm: 'sha256',
      fingerprint:
        '44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a',
      payload: {},
    })
    const file = new File([manifestText], 'lagos-fiscal-design.json', {
      type: 'application/json',
    })
    Object.defineProperty(file, 'text', {
      value: vi.fn().mockResolvedValue(manifestText),
    })

    fireEvent.change(screen.getByLabelText('Select downloaded manifest'), {
      target: { files: [file] },
    })

    await waitFor(() => {
      expect(screen.getByLabelText('Manifest JSON')).toHaveValue(manifestText)
    })
    expect(screen.getByText('Selected: lagos-fiscal-design.json')).toBeVisible()

    fireEvent.click(screen.getByRole('button', { name: 'Verify manifest' }))

    expect(await screen.findByText('Verified manifest')).toBeVisible()
  })

  it('keeps manual paste available as a fallback', async () => {
    render(<ManifestVerifier />)

    fireEvent.change(screen.getByLabelText('Manifest JSON'), {
      target: { value: '{not-json' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Verify manifest' }))

    expect(await screen.findByText('Invalid manifest')).toBeVisible()
  })
})
