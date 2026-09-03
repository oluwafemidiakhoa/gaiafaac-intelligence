import type { Metadata } from 'next'
import Link from 'next/link'

import { PageHeader } from '@/components/page-header'

export const metadata: Metadata = {
  title: 'Legal',
  description:
    'Legal notices, terms of service, and privacy policy for Gaia Fiscal Intelligence.',
}

export default function LegalPage() {
  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Legal"
        title="Terms & Policies"
        description="Legal framework and privacy policies for Gaia Fiscal Intelligence."
      />

      <div className="mt-12 space-y-12 max-w-4xl">
        {/* Disclaimer */}
        <section>
          <h2 className="font-bold text-2xl mb-4">Important Disclaimer</h2>
          <div className="rounded-lg border border-amber-200/30 bg-amber-50/30 p-6">
            <p className="text-sm text-foreground mb-4">
              <strong>GaiaFAAC Fiscal Intelligence is an independent, non-governmental research platform.</strong> It is not an official government service, and data published here should not be treated as official government financial records without independent verification.
            </p>
            <p className="text-sm text-foreground mb-4">
              All information on this platform is provided for research, educational, and informational purposes. While we employ rigorous verification, reconciliation, and human review processes, users should always verify critical financial information against official government sources before making institutional decisions.
            </p>
            <p className="text-sm text-foreground">
              Read our <Link href="/methodology" className="underline text-primary">methodology documentation</Link> to understand how we source, verify, and publish evidence before interpreting any record.
            </p>
          </div>
        </section>

        {/* Terms of Service */}
        <section>
          <h2 className="font-bold text-2xl mb-4">Terms of Service</h2>

          <div className="space-y-6 text-sm text-muted-foreground">
            <div>
              <h3 className="font-semibold text-foreground mb-2">1. Acceptance of Terms</h3>
              <p>
                By accessing and using GaiaFAAC Fiscal Intelligence, you agree to be bound by these terms and conditions. If you do not agree to any part of these terms, please do not use this platform.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-foreground mb-2">2. Use License</h3>
              <p>
                Permission is granted to temporarily access and view the materials (information and content) on GaiaFAAC for lawful purposes only. This is the grant of a license, not a transfer of title, and under this license you may not:
              </p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Modify or copy the materials</li>
                <li>Use the materials for any commercial purpose or for any public display</li>
                <li>Attempt to decompile or reverse engineer any software contained on the platform</li>
                <li>Remove any copyright or other proprietary notations from the materials</li>
                <li>Transfer the materials to another person or "mirror" the materials on any other server</li>
              </ul>
            </div>

            <div>
              <h3 className="font-semibold text-foreground mb-2">3. Disclaimer</h3>
              <p>
                The materials on GaiaFAAC are provided on an "as is" basis. GaiaFAAC makes no warranties, expressed or implied, and hereby disclaims and negates all other warranties including, without limitation, implied warranties or conditions of merchantability, fitness for a particular purpose, or non-infringement of intellectual property or other violation of rights.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-foreground mb-2">4. Limitations</h3>
              <p>
                In no event shall GaiaFAAC or its suppliers be liable for any damages (including, without limitation, damages for loss of data or profit, or due to business interruption) arising out of the use or inability to use the materials on the platform.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-foreground mb-2">5. Accuracy of Materials</h3>
              <p>
                While GaiaFAAC employs rigorous verification and review processes, we do not warrant that the materials on our platform are accurate, complete, or current. Materials may be outdated and we are under no obligation to update them.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-foreground mb-2">6. Links</h3>
              <p>
                GaiaFAAC has not reviewed all of the sites linked to its website and is not responsible for the contents of any such linked site. The inclusion of any link does not imply endorsement by GaiaFAAC of the site. Use of any such linked website is at the user's own risk.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-foreground mb-2">7. Modifications</h3>
              <p>
                GaiaFAAC may revise these terms and conditions without notice at any time. By using this website, you are agreeing to be bound by the then-current version of these terms and conditions.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-foreground mb-2">8. Governing Law</h3>
              <p>
                These terms and conditions are governed by and construed in accordance with the laws of Nigeria, and you irrevocably submit to the exclusive jurisdiction of the courts in that location.
              </p>
            </div>
          </div>
        </section>

        {/* Privacy Policy */}
        <section>
          <h2 className="font-bold text-2xl mb-4">Privacy Policy</h2>

          <div className="space-y-6 text-sm text-muted-foreground">
            <div>
              <h3 className="font-semibold text-foreground mb-2">Information We Collect</h3>
              <p>
                When you use GaiaFAAC, we may collect information about how you access and use the platform, including your IP address, browser type, pages visited, and search queries. For API access and institutional accounts, we collect contact information and usage metrics.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-foreground mb-2">How We Use Your Information</h3>
              <p>
                We use the information we collect to:
              </p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Improve and maintain our platform</li>
                <li>Provide customer support and respond to inquiries</li>
                <li>Monitor and analyze platform usage trends and patterns</li>
                <li>Detect and prevent fraudulent or unauthorized access</li>
                <li>Comply with applicable laws and regulations</li>
              </ul>
            </div>

            <div>
              <h3 className="font-semibold text-foreground mb-2">Data Security</h3>
              <p>
                We implement appropriate technical and organizational measures to protect your personal information against unauthorized access, alteration, disclosure, or destruction. However, no method of transmission over the Internet is 100% secure.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-foreground mb-2">Third-Party Services</h3>
              <p>
                GaiaFAAC may use third-party services for analytics, hosting, and other functions. These third parties are contractually obligated to use your personal information only as necessary to provide services to GaiaFAAC.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-foreground mb-2">Cookies</h3>
              <p>
                We use cookies and similar tracking technologies to enhance your experience on our platform. You can control cookie settings through your browser preferences, though some platform features may not function properly if cookies are disabled.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-foreground mb-2">Data Retention</h3>
              <p>
                We retain personal information only for as long as necessary to provide our services and comply with applicable laws. You may request deletion of your account and associated personal information by contacting us.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-foreground mb-2">Changes to This Policy</h3>
              <p>
                GaiaFAAC reserves the right to modify this privacy policy at any time. Changes will be effective immediately upon posting to the website. Your continued use of the platform constitutes your acceptance of the updated privacy policy.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-foreground mb-2">Contact Us</h3>
              <p>
                If you have questions about this privacy policy or our privacy practices, please contact us at privacy@gaiafaac.org.
              </p>
            </div>
          </div>
        </section>

        {/* Data Attribution */}
        <section>
          <h2 className="font-bold text-2xl mb-4">Data Attribution & Sources</h2>

          <p className="text-sm text-muted-foreground mb-4">
            All fiscal data published on GaiaFAAC is sourced from official government publications and organizations, including:
          </p>

          <ul className="space-y-2 text-sm text-muted-foreground list-disc list-inside">
            <li>Federal Account Allocation Committee (FAAC) official distributions</li>
            <li>Office of the Accountant General of the Federation (OAGF) records</li>
            <li>State and local government financial disclosures</li>
            <li>Official government statistical agencies and registries</li>
          </ul>

          <p className="text-sm text-muted-foreground mt-4">
            Detailed source attribution is preserved with every published record. See our <Link href="/sources" className="underline text-primary">Evidence Registry</Link> for complete lineage documentation.
          </p>
        </section>

        {/* CTA */}
        <section className="rounded-lg border border-border bg-muted/50 p-8">
          <h2 className="font-bold text-xl mb-4">Questions About Our Policies?</h2>
          <p className="text-muted-foreground mb-4">
            If you have concerns about how we handle data, our evidence standards, or any other legal matter, please contact our team.
          </p>
          <Link href="/contact" className="text-primary font-medium hover:underline">
            Contact Us →
          </Link>
        </section>
      </div>
    </div>
  )
}
