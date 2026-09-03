'use client'

import * as React from 'react'

interface TooltipContextValue {
  open: boolean
  setOpen: (open: boolean) => void
}

const TooltipContext = React.createContext<TooltipContextValue | undefined>(
  undefined,
)

function useTooltip() {
  const context = React.useContext(TooltipContext)
  if (!context) {
    throw new Error('Tooltip components must be used within TooltipProvider')
  }
  return context
}

interface TooltipProviderProps {
  children: React.ReactNode
}

function TooltipProvider({ children }: TooltipProviderProps) {
  const [open, setOpen] = React.useState(false)

  return (
    <TooltipContext.Provider value={{ open, setOpen }}>
      {children}
    </TooltipContext.Provider>
  )
}

interface TooltipTriggerProps extends React.HTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode
  asChild?: boolean
}

function TooltipTrigger({
  children,
  asChild,
  onMouseEnter,
  onMouseLeave,
  ...props
}: TooltipTriggerProps) {
  const { setOpen } = useTooltip()

  const handleMouseEnter = (e: React.MouseEvent<HTMLButtonElement>) => {
    setOpen(true)
    onMouseEnter?.(e)
  }

  const handleMouseLeave = (e: React.MouseEvent<HTMLButtonElement>) => {
    setOpen(false)
    onMouseLeave?.(e)
  }

  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(
      children as React.ReactElement<Record<string, unknown>>,
      {
        onMouseEnter: handleMouseEnter,
        onMouseLeave: handleMouseLeave,
        ...props,
      },
    )
  }

  return (
    <button
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      {...props}
    >
      {children}
    </button>
  )
}

interface TooltipContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

function TooltipContent({
  children,
  className,
  ...props
}: TooltipContentProps) {
  const { open } = useTooltip()

  if (!open) return null

  return (
    <div
      className={`absolute bottom-full left-1/2 z-50 mb-2 -translate-x-1/2 rounded-md bg-slate-900 px-3 py-2 text-xs whitespace-nowrap text-white ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}

export { TooltipProvider, TooltipTrigger, TooltipContent }
