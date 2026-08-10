'use client'

export function PrintButton() {
  return (
    <button
      type="button"
      onClick={() => window.print()}
      className="bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-medium print:hidden"
    >
      Print / Save PDF
    </button>
  )
}
