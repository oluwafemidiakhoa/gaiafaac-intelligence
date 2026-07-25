import { cn } from '@/lib/utils'

export function StatusPill({
  children,
  tone = 'neutral',
}: {
  children: React.ReactNode
  tone?: 'demo' | 'success' | 'neutral'
}) {
  return (
    <span
      className={cn(
        'inline-flex w-fit items-center rounded-full border px-2.5 py-1 font-mono text-[0.68rem] font-semibold tracking-wide uppercase',
        tone === 'demo' && 'border-amber-300 bg-amber-50 text-amber-900',
        tone === 'success' &&
          'border-emerald-200 bg-emerald-50 text-emerald-800',
        tone === 'neutral' && 'border-border bg-muted text-muted-foreground',
      )}
    >
      {children}
    </span>
  )
}
