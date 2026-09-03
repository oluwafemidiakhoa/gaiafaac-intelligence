'use client'

import { Activity, Fingerprint, Radio, ShieldCheck, Sparkles } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'

interface StateSignal {
  state_name: string
  state_slug: string
  net_allocation: string | null
}

interface FiscalCommandCanvasProps {
  total: string
  coverage: string
  period: string
  nationalChange: number | null
  topStates: StateSignal[]
}

const nodeCount = 24

function compactAmount(value: string | null) {
  if (!value) return 'Unavailable'
  const amount = Number(value)
  if (!Number.isFinite(amount)) return value
  if (Math.abs(amount) >= 1_000_000_000_000)
    return `₦${(amount / 1_000_000_000_000).toFixed(2)}T`
  if (Math.abs(amount) >= 1_000_000_000)
    return `₦${(amount / 1_000_000_000).toFixed(2)}B`
  if (Math.abs(amount) >= 1_000_000)
    return `₦${(amount / 1_000_000).toFixed(1)}M`
  return `₦${amount.toLocaleString('en-NG')}`
}

export function FiscalCommandCanvas({
  total,
  coverage,
  period,
  nationalChange,
  topStates,
}: FiscalCommandCanvasProps) {
  const [activeIndex, setActiveIndex] = useState(0)
  const nodes = useMemo(() => Array.from({ length: nodeCount }, (_, i) => i), [])
  const activeState = topStates.length
    ? topStates[activeIndex % topStates.length]
    : null

  useEffect(() => {
    if (topStates.length < 2) return
    const timer = window.setInterval(() => {
      setActiveIndex((value) => (value + 1) % topStates.length)
    }, 2800)
    return () => window.clearInterval(timer)
  }, [topStates.length])

  return (
    <div className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-[#071815]/90 p-4 shadow-[0_40px_120px_rgba(0,0,0,.45)] backdrop-blur-xl sm:p-5">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_45%,rgba(52,211,153,.15),transparent_32%),linear-gradient(rgba(255,255,255,.035)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.035)_1px,transparent_1px)] [background-size:auto,34px_34px,34px_34px]" />

      <div className="relative flex items-center justify-between gap-4 border-b border-white/10 pb-4">
        <div className="flex items-center gap-3">
          <span className="flex size-9 items-center justify-center rounded-xl border border-emerald-300/20 bg-emerald-300/10 text-emerald-200">
            <Radio className="size-4" />
          </span>
          <div>
            <p className="text-[0.65rem] font-bold tracking-[0.18em] text-emerald-200/60 uppercase">
              Gaia command mesh
            </p>
            <p className="mt-0.5 text-sm font-semibold text-white">Live governed signal</p>
          </div>
        </div>
        <span className="inline-flex items-center gap-2 rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-1 text-[0.68rem] font-bold text-emerald-100">
          <span className="size-1.5 animate-pulse rounded-full bg-emerald-300" />
          VERIFIED
        </span>
      </div>

      <div className="relative mt-4 grid gap-4 lg:grid-cols-[1fr_12rem]">
        <div className="relative min-h-[390px] overflow-hidden rounded-[1.5rem] border border-white/10 bg-[#03110f]/70">
          <div className="absolute inset-x-5 top-5 z-10 grid grid-cols-2 gap-2 sm:grid-cols-3">
            <div className="rounded-xl border border-white/10 bg-black/20 px-3 py-3 backdrop-blur">
              <p className="text-[0.58rem] tracking-[0.14em] text-white/35 uppercase">Published</p>
              <p className="mt-1 font-mono text-lg font-semibold text-white">{total}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-black/20 px-3 py-3 backdrop-blur">
              <p className="text-[0.58rem] tracking-[0.14em] text-white/35 uppercase">Coverage</p>
              <p className="mt-1 font-mono text-lg font-semibold text-white">{coverage}</p>
            </div>
            <div className="col-span-2 rounded-xl border border-white/10 bg-black/20 px-3 py-3 backdrop-blur sm:col-span-1">
              <p className="text-[0.58rem] tracking-[0.14em] text-white/35 uppercase">Momentum</p>
              <p className="mt-1 font-mono text-lg font-semibold text-white">
                {nationalChange === null
                  ? 'Awaiting'
                  : `${nationalChange >= 0 ? '+' : ''}${nationalChange.toFixed(1)}%`}
              </p>
            </div>
          </div>

          <div className="absolute inset-x-0 bottom-7 top-24 flex items-center justify-center">
            <div className="relative size-[270px] sm:size-[300px]">
              <div className="absolute inset-0 rounded-full border border-emerald-300/10" />
              <div className="absolute inset-7 rounded-full border border-dashed border-emerald-300/15" />
              <div className="absolute inset-16 rounded-full border border-emerald-300/20 bg-emerald-300/[0.025]" />

              {nodes.map((node) => {
                const angle = (node / nodeCount) * Math.PI * 2 - Math.PI / 2
                const radius = node % 3 === 0 ? 132 : node % 2 === 0 ? 118 : 105
                const x = 150 + Math.cos(angle) * radius
                const y = 150 + Math.sin(angle) * radius
                const isHot = node % 6 === activeIndex % 6
                return (
                  <span
                    key={node}
                    className={`absolute size-2.5 rounded-full border transition-all duration-700 ${
                      isHot
                        ? 'border-amber-200 bg-amber-300 shadow-[0_0_22px_rgba(252,211,77,.75)]'
                        : 'border-emerald-200/25 bg-emerald-300/25'
                    }`}
                    style={{ left: `${(x / 300) * 100}%`, top: `${(y / 300) * 100}%` }}
                  />
                )
              })}

              <div className="absolute left-1/2 top-1/2 flex size-24 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-[2rem] border border-emerald-200/25 bg-[#0b2a23] shadow-[0_0_80px_rgba(52,211,153,.12)]">
                <div className="text-center">
                  <Fingerprint className="mx-auto size-8 text-emerald-200" />
                  <span className="mt-1 block text-[0.55rem] font-bold tracking-[0.16em] text-emerald-100/60 uppercase">
                    Evidence
                  </span>
                </div>
              </div>

              <div className="absolute left-1/2 top-[7%] -translate-x-1/2 rounded-full border border-white/10 bg-[#061a16] px-2.5 py-1 text-[0.56rem] font-semibold text-white/55">SOURCE</div>
              <div className="absolute right-[2%] top-1/2 -translate-y-1/2 rounded-full border border-white/10 bg-[#061a16] px-2.5 py-1 text-[0.56rem] font-semibold text-white/55">REVIEW</div>
              <div className="absolute bottom-[5%] left-1/2 -translate-x-1/2 rounded-full border border-white/10 bg-[#061a16] px-2.5 py-1 text-[0.56rem] font-semibold text-white/55">PUBLISH</div>
              <div className="absolute left-[1%] top-1/2 -translate-y-1/2 rounded-full border border-white/10 bg-[#061a16] px-2.5 py-1 text-[0.56rem] font-semibold text-white/55">HASH</div>
            </div>
          </div>

          <div className="absolute bottom-3 left-4 right-4 flex items-center justify-between gap-3 border-t border-white/10 pt-3 text-[0.65rem] text-white/40">
            <span className="truncate">{period}</span>
            <span className="flex items-center gap-1.5 text-emerald-200/60">
              <ShieldCheck className="size-3" /> immutable trail
            </span>
          </div>
        </div>

        <div className="grid content-between gap-3">
          <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-4">
            <div className="flex items-center gap-2 text-[0.62rem] font-bold tracking-[0.14em] text-amber-200/65 uppercase">
              <Activity className="size-3.5" /> Signal feed
            </div>
            <p className="mt-4 text-sm font-semibold text-white">
              {activeState?.state_name ?? 'Governed publication'}
            </p>
            <p className="mt-1 font-mono text-lg font-semibold text-emerald-200">
              {activeState ? compactAmount(activeState.net_allocation) : total}
            </p>
            <p className="mt-3 text-xs leading-5 text-white/40">
              Ranked from published governed records only.
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-4">
            <div className="flex items-center gap-2 text-[0.62rem] font-bold tracking-[0.14em] text-emerald-200/65 uppercase">
              <Sparkles className="size-3.5" /> Ask Gaia
            </div>
            <p className="mt-3 text-xs leading-5 text-white/60">
              “What changed, where, and what evidence proves it?”
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
