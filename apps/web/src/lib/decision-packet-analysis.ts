/** Presentation checks only: never rewrites the published evidence or its status. */
export interface FiscalMonth {
  revenue_month: string
  gross_total: string | null
  total_deductions: string | null
  net_allocation: string | null
  proof_id: string
  proof_path: string
  source_organization: string
  source_sha256: string
  human_verified: boolean
  reconciliation_status: string
}

export function toKobo(value: unknown): bigint | null {
  if (typeof value !== 'string' || value.length > 80) return null
  const match = /^(-?)(\d+)(?:\.(\d{1,2}))?$/.exec(value)
  if (!match) return null
  const [, sign, whole, fraction = ''] = match
  const amount = BigInt(whole) * BigInt(100) + BigInt(fraction.padEnd(2, '0'))
  return sign ? -amount : amount
}

export function fromKobo(value: bigint): string {
  const amount = value < BigInt(0) ? -value : value
  return `${value < BigInt(0) ? '-' : ''}${amount / BigInt(100)}.${String(amount % BigInt(100)).padStart(2, '0')}`
}

/** Round percentages to two places using integer arithmetic, not float money. */
export function percentage(
  numerator: bigint,
  denominator: bigint,
): number | null {
  if (denominator <= BigInt(0)) return null
  const negative = numerator < BigInt(0)
  const magnitude = negative ? -numerator : numerator
  const rounded =
    (magnitude * BigInt(10000) + denominator / BigInt(2)) / denominator
  if (rounded > BigInt(Number.MAX_SAFE_INTEGER)) return null
  return (Number(rounded) / 100) * (negative ? -1 : 1)
}

export function monthName(period: string): string {
  return new Intl.DateTimeFormat('en-NG', {
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(`${period}T00:00:00Z`))
}

export function proofHref(month: FiscalMonth): string | null {
  return /^\/fiscal-proof\/[a-z0-9-]+\/\d{4}-\d{2}-\d{2}$/.test(
    month.proof_path,
  )
    ? month.proof_path
    : null
}

export function analyzeFiscalEvidence(
  months: readonly FiscalMonth[],
  year: number,
) {
  const valid = months.filter((month) =>
    new RegExp(`^${year}-(0[1-9]|1[0-2])-01$`).test(month.revenue_month),
  )
  const counts = new Map<string, number>()
  for (const month of valid) {
    counts.set(month.revenue_month, (counts.get(month.revenue_month) ?? 0) + 1)
  }
  const duplicatePeriods = [...counts].filter(([, n]) => n > 1).map(([p]) => p)
  const rows = valid
    .filter((month) => counts.get(month.revenue_month) === 1)
    .slice()
    .sort((a, b) => a.revenue_month.localeCompare(b.revenue_month))
    .map((month) => {
      const gross = toKobo(month.gross_total)
      const deductions = toKobo(month.total_deductions)
      const net = toKobo(month.net_allocation)
      const residual =
        gross !== null && deductions !== null && net !== null
          ? gross - deductions - net
          : null
      return {
        month,
        gross,
        deductions,
        net,
        residual,
        burden:
          gross !== null && deductions !== null
            ? percentage(deductions, gross)
            : null,
      }
    })
  const structurallyValid =
    valid.length === months.length && !duplicatePeriods.length
  const observed = rows.filter((row) => row.net !== null)
  const first = observed[0]
  const latest = observed.at(-1)
  const firstToLatest =
    structurallyValid &&
    observed.length >= 2 &&
    first &&
    latest &&
    first.net !== null &&
    latest.net !== null
      ? percentage(
          latest.net - first.net,
          first.net < BigInt(0) ? -first.net : first.net,
        )
      : null
  const prior = observed.length >= 6 ? observed.slice(-6, -3) : []
  const recent = observed.length >= 6 ? observed.slice(-3) : []
  const sumNet = (items: typeof rows) =>
    items.reduce((total, row) => total + (row.net ?? BigInt(0)), BigInt(0))
  const priorTotal = sumNet(prior)
  const recentTotal = sumNet(recent)
  const momentum =
    structurallyValid && prior.length === 3
      ? percentage(recentTotal - priorTotal, priorTotal)
      : null
  const sum = (key: 'gross' | 'deductions' | 'net') => {
    if (
      !structurallyValid ||
      !rows.length ||
      rows.some((row) => row[key] === null)
    ) {
      return null
    }
    return rows.reduce((total, row) => total + row[key]!, BigInt(0))
  }
  const slots = Array.from({ length: 12 }, (_, index) => {
    const period = `${year}-${String(index + 1).padStart(2, '0')}-01`
    return {
      period,
      conflict: duplicatePeriods.includes(period),
      row: rows.find((row) => row.month.revenue_month === period) ?? null,
    }
  })
  const invalidMoney = rows.some((row) =>
    [
      row.month.gross_total,
      row.month.total_deductions,
      row.month.net_allocation,
    ].some((value) => value !== null && toKobo(value) === null),
  )
  const residuals = rows.filter(
    (row) => row.residual !== null && row.residual !== BigInt(0),
  )
  const sourceCount = new Set(
    rows
      .map((row) => row.month.source_sha256)
      .filter((hash) => /^[0-9a-f]{64}$/i.test(hash))
      .map((hash) => hash.toLowerCase()),
  ).size
  return {
    rows,
    slots,
    first,
    latest,
    firstToLatest,
    prior,
    recent,
    momentum,
    totals: {
      gross: sum('gross'),
      deductions: sum('deductions'),
      net: sum('net'),
    },
    verifiedCount: rows.filter((row) => row.month.human_verified === true)
      .length,
    checkedCount: rows.filter((row) => row.residual !== null).length,
    residuals,
    sourceCount,
    invalidMoney,
    duplicatePeriods,
    invalidPeriodCount: months.length - valid.length,
    structurallyValid,
  }
}

export type FiscalAnalysis = ReturnType<typeof analyzeFiscalEvidence>
export type FiscalRow = FiscalAnalysis['rows'][number]
