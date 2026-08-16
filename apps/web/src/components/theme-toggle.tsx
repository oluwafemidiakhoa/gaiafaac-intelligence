'use client'

import { Moon, Sun } from 'lucide-react'
import { useEffect } from 'react'

export function ThemeToggle() {
  useEffect(() => {
    const stored = window.localStorage.getItem('gaiafaac-theme')
    const nextDark =
      stored === 'dark' ||
      (stored === null &&
        window.matchMedia('(prefers-color-scheme: dark)').matches)
    document.documentElement.classList.toggle('dark', nextDark)
  }, [])

  function toggleTheme() {
    const root = document.documentElement
    const nextDark = !root.classList.contains('dark')
    root.classList.toggle('dark', nextDark)
    window.localStorage.setItem('gaiafaac-theme', nextDark ? 'dark' : 'light')
  }

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="border-border bg-background hover:bg-muted inline-flex size-9 items-center justify-center rounded-md border transition-colors"
      aria-label="Toggle color theme"
      title="Toggle color theme"
    >
      <Moon className="size-4 dark:hidden" aria-hidden="true" />
      <Sun className="hidden size-4 dark:block" aria-hidden="true" />
    </button>
  )
}
