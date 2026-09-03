import Link from 'next/link'

export function SiteFooter() {
  return (
    <footer className="border-border mt-20 border-t bg-muted/30">
      <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8">
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {/* Platform */}
          <div>
            <h3 className="font-semibold text-foreground mb-4">Platform</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/terminal" className="text-muted-foreground hover:text-foreground transition">
                  Terminal
                </Link>
              </li>
              <li>
                <Link href="/live" className="text-muted-foreground hover:text-foreground transition">
                  Live Data
                </Link>
              </li>
              <li>
                <Link href="/fiscal-pulse" className="text-muted-foreground hover:text-foreground transition">
                  Intelligence
                </Link>
              </li>
              <li>
                <Link href="/sources" className="text-muted-foreground hover:text-foreground transition">
                  Evidence Registry
                </Link>
              </li>
            </ul>
          </div>

          {/* For Institutions */}
          <div>
            <h3 className="font-semibold text-foreground mb-4">For Institutions</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/api-access" className="text-muted-foreground hover:text-foreground transition">
                  API Access
                </Link>
              </li>
              <li>
                <Link href="/decision-packets" className="text-muted-foreground hover:text-foreground transition">
                  Decision Support
                </Link>
              </li>
              <li>
                <Link href="/audit-tools" className="text-muted-foreground hover:text-foreground transition">
                  Audit Tools
                </Link>
              </li>
              <li>
                <Link href="/pricing" className="text-muted-foreground hover:text-foreground transition">
                  Pricing
                </Link>
              </li>
            </ul>
          </div>

          {/* Learn */}
          <div>
            <h3 className="font-semibold text-foreground mb-4">Learn</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/methodology" className="text-muted-foreground hover:text-foreground transition">
                  Methodology
                </Link>
              </li>
              <li>
                <Link href="/documentation" className="text-muted-foreground hover:text-foreground transition">
                  Documentation
                </Link>
              </li>
              <li>
                <a
                  href="https://github.com/oluwafemidiakhoa/gaiafaac-intelligence"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-muted-foreground hover:text-foreground transition"
                >
                  Source Code
                </a>
              </li>
            </ul>
          </div>

          {/* Company */}
          <div>
            <h3 className="font-semibold text-foreground mb-4">Company</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/about" className="text-muted-foreground hover:text-foreground transition">
                  About
                </Link>
              </li>
              <li>
                <Link href="/contact" className="text-muted-foreground hover:text-foreground transition">
                  Contact
                </Link>
              </li>
              <li>
                <Link href="/legal" className="text-muted-foreground hover:text-foreground transition">
                  Legal
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom section */}
        <div className="border-t border-border mt-8 pt-8">
          <p className="text-muted-foreground text-xs">
            Gaia Fiscal Intelligence is an independent research platform, not an official government service.
          </p>
          <p className="text-muted-foreground text-xs mt-2">
            <Link href="/methodology" className="hover:text-foreground underline">
              Read the methodology
            </Link>{' '}
            before interpreting any record.
          </p>
        </div>
      </div>
    </footer>
  )
}
