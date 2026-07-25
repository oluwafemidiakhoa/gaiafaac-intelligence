import { describe, expect, it } from 'vitest'

import { formatNaira } from './format'

describe('formatNaira', () => {
  it('formats exact decimal strings without floating-point conversion', () => {
    expect(formatNaira('1234567890123456789012.34')).toBe(
      '₦1,234,567,890,123,456,789,012.34',
    )
    expect(formatNaira('-1000.50')).toBe('-₦1,000.50')
    expect(formatNaira(null)).toBe('Unavailable')
  })
})
