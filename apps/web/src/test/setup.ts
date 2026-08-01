import '@testing-library/jest-dom/vitest'

import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// Vitest is not configured with `globals: true`, so Testing Library's automatic
// per-test cleanup never registers. Unmount rendered trees between tests so DOM
// from one test cannot leak into the next (which would make queries find
// duplicate or stale elements across tests in the same file).
afterEach(() => {
  cleanup()
})
