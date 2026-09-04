import { ArrowUpRight, ShieldCheck } from 'lucide-react'
import Link from 'next/link'

const product = [
  ['Terminal', '/terminal'],
  ['Live data', '/live'],
  ['Intelligence', '/fiscal-pulse'],
  ['Evidence', '/sources'],
  ['Review', '/review'],
]

const commercial = [
  ['Institutions', '/institutional'],
  ['Pricing', '/pricing'],
  ['Account', '/account'],
  ['Request Watch', '/pilot'],
]

export function SiteFooter() {
  return (
    <footer className="mt-24 border-t border-white/8 bg-[#041915] text-white">
      <div className="gaia-shell grid gap-12 py-12 lg:grid-cols-[1.2fr_.8fr_.8fr] lg:py-16">
        <div className="max-w-xl">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-xl bg-amber-300 font-mono text-xs font-black text-teal-950">
              GF
            </div>
            <div>
              <p className="font-semibold tracking-tight">
                Gaia Fiscal Intelligence
              </p>
              <p className="mt-0.5 font-mono text-[0.6rem] tracking-[0.16em] text-emerald-200/55 uppercase">
                Governed public-finance intelligence
              </p>
            </div>
          </div>
          <p className="mt-6 max-w-lg text-sm leading-7 text-white/55">
            An independent evidence and decision layer for Nigerian public
            finance. Official records remain source-linked, review-gated, and
            auditable from publication through institutional use.
          </p>
          <div className="mt-6 inline-flex items-center gap-2 rounded-full border border-emerald-300/15 bg-emerald-300/[0.06] px-3 py-1.5 text-xs font-medium text-emerald-100/75">
            <ShieldCheck className="size-3.5" />
            Evidence before inference
          </div>
        </div>

        <div>
          <p className="font-mono text-[0.65rem] font-semibold tracking-[0.18em] text-white/35 uppercase">
            Control plane
          </p>
          <nav className="mt-4 grid gap-3">
            {product.map(([label, href]) => (
              <Link
                key={href}
                href={href}
                className="text-sm text-white/65 transition hover:text-white"
              >
                {label}
              </Link>
            ))}
          </nav>
        </div>

        <div>
          <p className="font-mono text-[0.65rem] font-semibold tracking-[0.18em] text-white/35 uppercase">
            Commercial
          </p>
          <nav className="mt-4 grid gap-3">
            {commercial.map(([label, href]) => (
              <Link
                key={href}
                href={href}
                className="text-sm text-white/65 transition hover:text-white"
              >
                {label}
              </Link>
            ))}
          </nav>
        </div>
      </div>

      <div className="border-t border-white/8">
        <div className="gaia-shell flex flex-col gap-4 py-5 text-xs text-white/35 sm:flex-row sm:items-center sm:justify-between">
          <p>
            Independent research platform · Not an official government service.
          </p>
          <Link
            href="/methodology"
            className="inline-flex items-center gap-1.5 font-medium text-white/55 transition hover:text-white"
          >
            Methodology & interpretation
            <ArrowUpRight className="size-3.5" />
          </Link>
        </div>
      </div>
    </footer>
  )
}
