import { GeistMono } from 'geist/font/mono'
import { GeistSans } from 'geist/font/sans'
import type { Metadata } from 'next'

import { SiteFooter } from '@/components/site-footer'
import { SiteHeader } from '@/components/site-header'

import './globals.css'

export const metadata: Metadata = {
  title: {
    default: 'Gaia Fiscal Intelligence',
    template: '%s | Gaia Fiscal Intelligence',
  },
  description:
    'Verified public-finance data, evidence and fiscal events for Nigeria.',
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
