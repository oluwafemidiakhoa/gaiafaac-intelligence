'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Check, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

export default function PricingPage() {
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'annual'>('monthly');

  const tiers = [
    {
      name: 'Free',
      slug: 'free',
      price: 0,
      period: 'Forever free',
      description: 'For explorers and researchers',
      cta: 'Start Free',
      highlighted: false,
      features: {
        included: [
          'Public FAAC explorer',
          'Basic search & filters',
          '10,000 API requests/month',
          'Community support',
          'Read-only access',
        ],
        excluded: [
          'Watchlists & alerts',
          'CSV/JSON exports',
          'Decision Packets',
          'Webhooks',
          'Dedicated support',
        ],
      },
    },
    {
      name: 'Professional',
      slug: 'professional',
      price: 50_000,
      period: '/month',
      description: 'For institutions & analysts',
      cta: 'Subscribe Now',
      highlighted: true,
      features: {
        included: [
          'Everything in Free',
          'Unlimited watchlists',
          'Email alerts on fiscal changes',
          '100,000 API requests/month',
          '5 CSV/JSON exports/month',
          'Decision Packets (2/month)',
          'Email support',
        ],
        excluded: [
          'Webhooks',
          'Unlimited exports',
          'SLA guarantee',
          'Dedicated account manager',
        ],
      },
    },
    {
      name: 'Enterprise',
      slug: 'enterprise',
      price: 500_000,
      period: '/month',
      description: 'For banks, governments, APIs',
      cta: 'Contact Sales',
      highlighted: false,
      features: {
        included: [
          'Everything in Professional',
          'Unlimited API requests',
          'Unlimited exports',
          'Webhook integrations',
          'Custom report generation',
          'Decision Packets (unlimited)',
          'Financial data API',
          '99.9% SLA guarantee',
          'Dedicated account manager',
          'Custom integrations',
          'Priority support (phone/email)',
        ],
        excluded: [],
      },
    },
  ];

  const comparisonFeatures = [
    {
      category: 'Core Features',
      items: [
        { name: 'Public FAAC Data', free: true, pro: true, enterprise: true },
        {
          name: 'Watchlists & Alerts',
          free: false,
          pro: true,
          enterprise: true,
        },
        {
          name: 'Decision Packets',
          free: false,
          pro: '2/month',
          enterprise: 'Unlimited',
        },
      ],
    },
    {
      category: 'API & Integration',
      items: [
        {
          name: 'API Access',
          free: '10K/mo',
          pro: '100K/mo',
          enterprise: 'Unlimited',
        },
        {
          name: 'Webhooks',
          free: false,
          pro: false,
          enterprise: true,
        },
        {
          name: 'Custom Integrations',
          free: false,
          pro: false,
          enterprise: true,
        },
      ],
    },
    {
      category: 'Support',
      items: [
        { name: 'Community Support', free: true, pro: true, enterprise: true },
        {
          name: 'Email Support',
          free: false,
          pro: true,
          enterprise: true,
        },
        {
          name: 'Priority Support',
          free: false,
          pro: false,
          enterprise: true,
        },
        { name: 'SLA Guarantee', free: false, pro: false, enterprise: true },
      ],
    },
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <div className="bg-gradient-to-br from-green-50 to-blue-50 px-4 py-16 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-4xl text-center">
          <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl">
            Verified Fiscal Intelligence Pricing
          </h1>
          <p className="mt-6 text-xl text-gray-600">
            Every government number, traceable. Every number, proven.
          </p>
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="px-4 py-16 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
            {tiers.map((tier) => (
              <div
                key={tier.slug}
                className={`relative rounded-2xl transition-all ${
                  tier.highlighted
                    ? 'ring-2 ring-green-500 shadow-xl'
                    : 'shadow-lg'
                }`}
              >
                {tier.highlighted && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-green-500 text-white px-4 py-1 rounded-full text-sm font-semibold">
                    Most Popular
                  </div>
                )}

                <div className={`p-8 rounded-2xl h-full ${
                  tier.highlighted ? 'bg-green-50' : 'bg-white'
                }`}>
                  <h3 className="text-2xl font-bold text-gray-900">
                    {tier.name}
                  </h3>
                  <p className="mt-2 text-sm text-gray-600">{tier.description}</p>

                  <div className="mt-6">
                    <div className="flex items-baseline gap-2">
                      <span className="text-5xl font-bold text-gray-900">
                        ₦{tier.price.toLocaleString()}
                      </span>
                      <span className="text-gray-600">{tier.period}</span>
                    </div>
                  </div>

                  <button
                    className={`w-full mt-8 px-4 py-3 rounded-lg font-semibold transition-all ${
                      tier.highlighted
                        ? 'bg-green-500 text-white hover:bg-green-600'
                        : tier.slug === 'enterprise'
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                    }`}
                  >
                    {tier.cta}
                  </button>

                  {/* Features */}
                  <div className="mt-8 space-y-4">
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-4">
                        Included
                      </h4>
                      <ul className="space-y-3">
                        {tier.features.included.map((feature) => (
                          <li key={feature} className="flex gap-3">
                            <Check className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                            <span className="text-gray-700">{feature}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {tier.features.excluded.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-4">
                          Not included
                        </h4>
                        <ul className="space-y-3">
                          {tier.features.excluded.map((feature) => (
                            <li key={feature} className="flex gap-3">
                              <X className="h-5 w-5 text-gray-300 flex-shrink-0 mt-0.5" />
                              <span className="text-gray-500">{feature}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Feature Comparison Table */}
      <div className="px-4 py-16 sm:px-6 lg:px-8 bg-gray-50">
        <div className="mx-auto max-w-7xl">
          <h2 className="text-3xl font-bold text-gray-900 mb-12">
            Detailed Comparison
          </h2>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b-2 border-gray-200">
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                    Feature
                  </th>
                  <th className="px-6 py-3 text-center text-sm font-semibold text-gray-900">
                    Free
                  </th>
                  <th className="px-6 py-3 text-center text-sm font-semibold text-gray-900">
                    Professional
                  </th>
                  <th className="px-6 py-3 text-center text-sm font-semibold text-gray-900">
                    Enterprise
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {comparisonFeatures.map((section) => (
                  <div key={section.category}>
                    <tr className="bg-gray-100">
                      <td
                        colSpan={4}
                        className="px-6 py-3 text-sm font-semibold text-gray-900"
                      >
                        {section.category}
                      </td>
                    </tr>
                    {section.items.map((item) => (
                      <tr key={item.name} className="hover:bg-gray-50">
                        <td className="px-6 py-3 text-sm text-gray-900">
                          {item.name}
                        </td>
                        <td className="px-6 py-3 text-center">
                          {item.free === true ? (
                            <Check className="h-5 w-5 text-green-500 mx-auto" />
                          ) : item.free === false ? (
                            <X className="h-5 w-5 text-gray-300 mx-auto" />
                          ) : (
                            <span className="text-sm text-gray-600">
                              {item.free}
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-3 text-center">
                          {item.pro === true ? (
                            <Check className="h-5 w-5 text-green-500 mx-auto" />
                          ) : item.pro === false ? (
                            <X className="h-5 w-5 text-gray-300 mx-auto" />
                          ) : (
                            <span className="text-sm text-gray-600">
                              {item.pro}
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-3 text-center">
                          {item.enterprise === true ? (
                            <Check className="h-5 w-5 text-green-500 mx-auto" />
                          ) : item.enterprise === false ? (
                            <X className="h-5 w-5 text-gray-300 mx-auto" />
                          ) : (
                            <span className="text-sm text-gray-600">
                              {item.enterprise}
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </div>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* FAQ Section */}
      <div className="px-4 py-16 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl">
          <h2 className="text-3xl font-bold text-gray-900 mb-12">
            Frequently Asked Questions
          </h2>

          <div className="space-y-8">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Can I change my plan anytime?
              </h3>
              <p className="text-gray-600">
                Yes! You can upgrade or downgrade at any time. Changes take
                effect on your next billing cycle.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Do you offer annual billing discounts?
              </h3>
              <p className="text-gray-600">
                Contact our sales team for custom pricing if you commit to an
                annual plan.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                What payment methods do you accept?
              </h3>
              <p className="text-gray-600">
                We accept all major credit/debit cards and Paystack for Nigerian
                customers.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Is there a free trial for paid plans?
              </h3>
              <p className="text-gray-600">
                Yes! We offer a 14-day free trial for Professional and Enterprise
                plans.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Do you offer refunds?
              </h3>
              <p className="text-gray-600">
                We offer a 14-day money-back guarantee. Contact support if you need to cancel.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-gradient-to-r from-green-500 to-blue-600 px-4 py-16 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="text-3xl font-bold text-white mb-6">
            Ready to access verified fiscal intelligence?
          </h2>
          <p className="text-xl text-green-50 mb-8">
            Join institutions and auditors who trust GaiaFAAC for fiscal evidence.
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/auth/signup?tier=professional">
              <Button className="bg-white text-green-600 hover:bg-gray-50 text-lg px-8 py-3">
                Start Free Trial
              </Button>
            </Link>
            <Link href="/contact">
              <Button className="border-2 border-white text-white hover:bg-white/10 text-lg px-8 py-3">
                Contact Sales
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
