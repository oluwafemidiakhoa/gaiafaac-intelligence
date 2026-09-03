import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Legal',
  description:
    'Legal notices, terms of service, and privacy policy for Gaia Fiscal Intelligence.',
}

export default function LegalPage() {
  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <div className="mt-8 space-y-20 max-w-4xl">
        {/* Critical Disclaimer */}
        <section className="rounded-lg border-2 border-amber-400/40 bg-gradient-to-r from-amber-50/50 to-orange-50/30 p-8">
          <div className="text-xs font-bold text-amber-400 tracking-widest mb-4">IMPORTANT DISCLAIMER</div>
          <h1 className="font-serif text-4xl font-bold mb-6 text-foreground">
            Not an official government platform
          </h1>
          <p className="text-muted-foreground mb-4 leading-relaxed">
            <strong>GaiaFAAC Fiscal Intelligence is an independent, non-governmental research platform.</strong> It is not an official government service, and data published here should not be treated as official government financial records without independent verification against authoritative sources.
          </p>
          <p className="text-muted-foreground mb-4 leading-relaxed">
            All information is provided for research, educational, and informational purposes. Users must independently verify critical financial information against official government sources before making institutional or investment decisions.
          </p>
          <p className="text-muted-foreground leading-relaxed">
            Read our <Link href="/methodology" className="underline text-primary font-medium">methodology documentation</Link> before interpreting any record.
          </p>
        </section>

        {/* Terms Overview */}
        <section>
          <div className="mb-8">
            <div className="text-xs font-bold text-amber-400 tracking-widest mb-3">LEGAL FRAMEWORK</div>
            <h2 className="font-serif text-4xl font-bold leading-tight text-foreground">
              Terms & policies
            </h2>
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            <div className="border-l-4 border-teal-600 pl-6 py-6">
              <div className="text-sm font-bold text-teal-600 tracking-widest mb-3">TERMS OF SERVICE</div>
              <p className="text-muted-foreground text-sm leading-relaxed mb-4">
                By using GaiaFAAC, you agree to our terms. We grant a license for personal, non-commercial use. All materials provided on "as is" basis. We make no warranties about accuracy, completeness, or fitness for purpose.
              </p>
              <div className="text-xs text-muted-foreground">Governed by laws of Nigeria</div>
            </div>
            <div className="border-l-4 border-teal-600 pl-6 py-6">
              <div className="text-sm font-bold text-teal-600 tracking-widest mb-3">PRIVACY POLICY</div>
              <p className="text-muted-foreground text-sm leading-relaxed mb-4">
                We collect information about platform usage (IP, browser, pages visited). For API and institutional accounts, we collect contact information and usage metrics. All data is protected with industry-standard security measures.
              </p>
              <div className="text-xs text-muted-foreground">privacy@gaiafaac.org for inquiries</div>
            </div>
          </div>
        </section>

        {/* Key Provisions */}
        <section className="border-t border-b border-border py-16">
          <div className="mb-12">
            <div className="text-xs font-bold text-amber-400 tracking-widest mb-3">PROVISIONS</div>
            <h2 className="font-serif text-4xl font-bold leading-tight text-foreground">
              Key terms
            </h2>
          </div>
          <div className="space-y-6">
            <div className="border-l-4 border-amber-400/30 pl-6 py-4">
              <div className="text-sm font-semibold text-foreground mb-2">Use License</div>
              <p className="text-sm text-muted-foreground">
                Personal, non-commercial use only. No modification, copying, decompilation, or redistribution. No commercial display or resale of materials.
              </p>
            </div>
            <div className="border-l-4 border-amber-400/30 pl-6 py-4">
              <div className="text-sm font-semibold text-foreground mb-2">Disclaimer</div>
              <p className="text-sm text-muted-foreground">
                Materials provided "as is." GaiaFAAC makes no warranties about accuracy, merchantability, fitness for purpose, or non-infringement. Materials may be outdated.
              </p>
            </div>
            <div className="border-l-4 border-amber-400/30 pl-6 py-4">
              <div className="text-sm font-semibold text-foreground mb-2">Limitations</div>
              <p className="text-sm text-muted-foreground">
                GaiaFAAC is not liable for damages from use or inability to use platform materials, including loss of data or profit, or business interruption.
              </p>
            </div>
            <div className="border-l-4 border-amber-400/30 pl-6 py-4">
              <div className="text-sm font-semibold text-foreground mb-2">Data Retention</div>
              <p className="text-sm text-muted-foreground">
                Personal information retained only as long as necessary for services and legal compliance. Request deletion by contacting privacy@gaiafaac.org.
              </p>
            </div>
            <div className="border-l-4 border-amber-400/30 pl-6 py-4">
              <div className="text-sm font-semibold text-foreground mb-2">Modifications</div>
              <p className="text-sm text-muted-foreground">
                GaiaFAAC may revise terms at any time. Continued use constitutes acceptance of current terms. Check this page regularly for updates.
              </p>
            </div>
          </div>
        </section>

        {/* Data Attribution */}
        <section>
          <div className="mb-8">
            <div className="text-xs font-bold text-amber-400 tracking-widest mb-3">SOURCES</div>
            <h2 className="font-serif text-3xl font-bold text-foreground">
              Data attribution
            </h2>
          </div>
          <p className="text-muted-foreground mb-6 leading-relaxed">
            All fiscal data published on GaiaFAAC is sourced from official government publications and organizations:
          </p>
          <ul className="space-y-3 text-sm text-muted-foreground">
            <li className="flex items-start gap-3">
              <span className="text-amber-400 font-bold">•</span>
              <span>Federal Account Allocation Committee (FAAC) official distributions</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-amber-400 font-bold">•</span>
              <span>Office of the Accountant General of the Federation (OAGF) records</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-amber-400 font-bold">•</span>
              <span>State and local government financial disclosures</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-amber-400 font-bold">•</span>
              <span>Official government statistical agencies and registries</span>
            </li>
          </ul>
          <p className="text-sm text-muted-foreground mt-6">
            Detailed source attribution preserved with every record. See our <Link href="/sources" className="underline text-primary">Evidence Registry</Link> for complete lineage.
          </p>
        </section>

        {/* Contact */}
        <section className="border-t border-border pt-16 text-center">
          <h2 className="font-serif text-3xl font-bold mb-4 text-foreground">Questions or concerns?</h2>
          <p className="text-muted-foreground mb-6">
            Contact us about legal, privacy, evidence standards, or any policy matters.
          </p>
          <Link href="/contact" className="text-primary font-medium hover:underline">
            Contact us →
          </Link>
        </section>
      </div>
    </div>
  )
}
