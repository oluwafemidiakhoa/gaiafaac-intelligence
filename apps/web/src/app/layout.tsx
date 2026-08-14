import { GeistMono } from 'geist/font/mono'
import { GeistSans } from 'geist/font/sans'
import type { Metadata } from 'next'

import { SiteFooter } from '@/components/site-footer'
import { SiteHeader } from '@/components/site-header'

import './globals.css'

export const metadata: Metadata = {
  title: {
    default: 'GaiaFAAC',
    template: '%s | GaiaFAAC',
  },
  description:
    'The verifiable fiscal ledger for Nigeria: sourced, reconciled, versioned public-finance evidence.',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html
      lang="en"
      data-scroll-behavior="smooth"
      className={`${GeistSans.variable} ${GeistMono.variable}`}
    >
      <body className="bg-background text-foreground min-h-screen font-sans antialiased">
        <SiteHeader />
        <main>{children}</main>
        <SiteFooter />
      </body>
    </html>
  )
}
