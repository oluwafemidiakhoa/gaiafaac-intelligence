'use client'

import { Moon, Sun } from 'lucide-react'
import { useEffect, useState } from 'react'

export function ThemeToggle() {
  const [dark, setDark] = useState(false)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const stored = window.localStorage.getItem('gaiafaac-theme')
    const nextDark =
      stored === 'dark' ||
      (stored === null && window.matchMedia('(prefers-color-scheme: dark)').matches)
    document.documentElement.classList.toggle('dark', nextDark)
    setDark(nextDark)
    setReady(true)
  }, [])

  function toggleTheme() {
    const nextDark = !dark
    document.documentElement.classList.toggle('dark', nextDark)
    window.localStorage.setItem('gaiafaac-theme', nextDark ? 'dark' : 'light')
    setDark(nextDark)
  }

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="border-border bg-background hover:bg-muted inline-flex size-9 items-center justify-center rounded-md border transition-colors"
      aria-label={dark ? 'Use light theme' : 'Use dark theme'}
      title={dark ? 'Use light theme' : 'Use dark theme'}
    >
      {ready && dark ? (
        <Sun className="size-4" aria-hidden="true" />
      ) : (
        <Moon className="size-4" aria-hidden="true" />
      )}
    </button>
  )
}
