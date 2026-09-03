import * as React from 'react'

import { cn } from '@/lib/utils'

function Card({ className, ...props }: React.ComponentProps<'div'>) {
  return (
    <div
      data-slot="card"
      className={cn(
        'border-border/80 bg-card/94 text-card-foreground rounded-2xl border shadow-[0_16px_48px_rgba(3,44,39,0.065)] backdrop-blur-xl transition-[border-color,box-shadow,transform] duration-200 hover:border-primary/20 hover:shadow-[0_22px_65px_rgba(3,44,39,0.09)]',
        className,
      )}
      {...props}
    />
  )
}

function CardHeader({ className, ...props }: React.ComponentProps<'div'>) {
  return (
    <div
      data-slot="card-header"
      className={cn('flex flex-col gap-2 p-6 sm:p-7', className)}
      {...props}
    />
  )
}

function CardTitle({ className, ...props }: React.ComponentProps<'h2'>) {
  return (
    <h2
      data-slot="card-title"
      className={cn('font-semibold tracking-[-0.025em]', className)}
      {...props}
    />
  )
}

function CardDescription({ className, ...props }: React.ComponentProps<'p'>) {
  return (
    <p
      data-slot="card-description"
      className={cn('text-muted-foreground text-sm leading-6', className)}
      {...props}
    />
  )
}

function CardContent({ className, ...props }: React.ComponentProps<'div'>) {
  return (
    <div
      data-slot="card-content"
      className={cn('px-6 pb-6 sm:px-7 sm:pb-7', className)}
      {...props}
    />
  )
}

export { Card, CardContent, CardDescription, CardHeader, CardTitle }
