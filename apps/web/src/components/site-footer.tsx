import Link from 'next/link'

export function SiteFooter() {
  return (
    <footer className="border-border mt-20 border-t">
      <div className="text-muted-foreground mx-auto grid max-w-7xl gap-5 px-5 py-10 text-sm leading-6 md:grid-cols-2 lg:px-8">
        <p>
          GaiaFAAC Intelligence is an independent research platform, not an
          official government service.
        </p>
        <p className="md:text-right">
          <Link href="/methodology" className="hover:text-foreground underline">
            Read the methodology
          </Link>{' '}
          before interpreting any record.
        </p>
      </div>
    </footer>
  )
}
