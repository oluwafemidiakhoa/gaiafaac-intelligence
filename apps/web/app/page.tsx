'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      {/* Navigation */}
      <nav className="border-b border-gray-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="text-2xl font-bold text-green-600">GaiaFAAC</div>
            <div className="flex gap-4">
              <Link href="/pricing">
                <Button variant="ghost">Pricing</Button>
              </Link>
              <Link href="/auth/signup">
                <Button>Sign Up</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          <h1 className="text-5xl sm:text-6xl font-bold tracking-tight text-gray-900 mb-6">
            Verified Fiscal Intelligence for Nigeria
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Every government number, traceable. Every number, proven.
            Access institutional-grade fiscal data with provenance, reconciliation, and evidence.
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/auth/signup?tier=professional">
              <Button size="lg" className="bg-green-600 hover:bg-green-700">
                Start Free Trial
              </Button>
            </Link>
            <Link href="/pricing">
              <Button size="lg" variant="outline">
                View Pricing
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="bg-white py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            Why GaiaFAAC
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="text-4xl mb-4">🔐</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Verified Evidence</h3>
              <p className="text-gray-600">
                Every fiscal record is traced from official source to publication with SHA-256 hashing and human review.
              </p>
            </div>
            <div className="text-center">
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Institutional APIs</h3>
              <p className="text-gray-600">
                RESTful APIs, Decision Packets, webhooks, and custom exports for banks, governments, and analysts.
              </p>
            </div>
            <div className="text-center">
              <div className="text-4xl mb-4">⚡</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Real-time Reconciliation</h3>
              <p className="text-gray-600">
                Monitor fiscal anomalies, conflicting sources, and revisions as they happen.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-gradient-to-r from-green-500 to-blue-600 py-16">
        <div className="mx-auto max-w-3xl text-center px-4">
          <h2 className="text-3xl font-bold text-white mb-6">
            Ready to access verified fiscal intelligence?
          </h2>
          <div className="flex gap-4 justify-center">
            <Link href="/auth/signup?tier=professional">
              <Button size="lg" className="bg-white text-green-600 hover:bg-gray-50">
                Start Free Trial
              </Button>
            </Link>
            <Link href="/pricing">
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white/10">
                View Plans
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="bg-gray-900 text-gray-400 py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center">
          <p>&copy; 2026 GaiaFAAC Intelligence. Nigerian fiscal evidence infrastructure.</p>
        </div>
      </div>
    </div>
  );
}
