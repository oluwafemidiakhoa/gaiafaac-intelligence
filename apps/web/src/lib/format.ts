export function formatNaira(value: string | null): string {
  if (value === null) return 'Unavailable'
  const match = /^(-?)(\d+)(?:\.(\d{1,2}))?$/.exec(value)
  if (!match) return 'Unavailable'
  const [, sign, integer, fraction = ''] = match
  const grouped = integer.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  return `${sign}₦${grouped}.${fraction.padEnd(2, '0')}`
}

export function formatDate(value: string | null): string {
  if (value === null) return 'Not provided'
  return new Intl.DateTimeFormat('en-NG', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(`${value}T00:00:00Z`))
}

export function humanize(value: string): string {
  return value.replaceAll('_', ' ')
}
