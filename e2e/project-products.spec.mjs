import { expect, test } from '@playwright/test'

const purchaseId = '11111111-2222-4333-8444-555555555555'

const products = [
  {
    code: 'decision_pack',
    label: 'Individual Decision Pack',
    billing_mode: 'one_time',
    description: 'Governed evidence for one jurisdiction and evidence year.',
    price_naira: 50000,
  },
  {
    code: 'multi_state_comparison_pack',
    label: 'Multi-State Comparison Pack',
    billing_mode: 'one_time',
    description: 'Governed comparison across multiple jurisdictions.',
    price_naira: 100000,
  },
  {
    code: 'historical_evidence_export',
    label: 'Historical Fiscal Evidence Export',
    billing_mode: 'one_time',
    description: 'Governed historical evidence export.',
    price_naira: 75000,
  },
  {
    code: 'due_diligence_snapshot',
    label: 'Due-Diligence Evidence Snapshot',
    billing_mode: 'one_time',
    description: 'Governed point-in-time due-diligence evidence snapshot.',
    price_naira: 150000,
  },
]

const purchases = [
  {
    id: purchaseId,
    product_code: 'decision_pack',
    amount_naira: '50000.00',
    currency: 'NGN',
    status: 'success',
    fulfillment_status: 'ready',
    fulfillment_reference: `/api/v1/billing/one-time/purchases/${purchaseId}/fulfillment`,
    completed_at: '2026-09-05T23:00:00Z',
    created_at: '2026-09-05T22:55:00Z',
  },
]

async function mockProjectProducts(page) {
  await page.route('**/api/customer/commercial/products', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(products),
    })
  })
  await page.route(
    '**/api/customer/billing/one-time/purchases',
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(purchases),
      })
    },
  )
}

test.describe('Project Products commercial delivery', () => {
  test('Project Products is visible in the commercial navigation', async ({
    page,
  }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' })

    const link = page
      .getByRole('link', { name: 'Project Products', exact: true })
      .first()
    await expect(link).toBeVisible()
    await expect(link).toHaveAttribute('href', '/projects')
  })

  test('paid ready order exposes Excel, PDF and governed JSON downloads', async ({
    page,
  }) => {
    await mockProjectProducts(page)
    await page.goto('/projects', { waitUntil: 'domcontentloaded' })

    await expect(
      page.getByText('One-time purchase + fulfillment', { exact: true }),
    ).toBeVisible()
    await expect(
      page.getByRole('heading', { name: 'Project Products', exact: true }),
    ).toBeVisible()
    await expect(page.getByText('1. Buy once', { exact: true })).toBeVisible()
    await expect(
      page.getByText('2. Fulfillment freezes', { exact: true }),
    ).toBeVisible()
    await expect(
      page.getByText('3. Download deliverables', { exact: true }),
    ).toBeVisible()

    const excel = page.getByRole('link', {
      name: 'Download Excel',
      exact: true,
    })
    const pdf = page.getByRole('link', {
      name: 'Download PDF',
      exact: true,
    })
    const json = page.getByRole('link', { name: 'Open JSON', exact: true })

    await expect(excel).toBeVisible()
    await expect(excel).toHaveAttribute(
      'href',
      `/api/customer/billing/one-time/purchases/${purchaseId}/download.xlsx`,
    )
    await expect(pdf).toBeVisible()
    await expect(pdf).toHaveAttribute(
      'href',
      `/api/customer/billing/one-time/purchases/${purchaseId}/download.pdf`,
    )
    await expect(json).toBeVisible()
    await expect(json).toHaveAttribute(
      'href',
      `/api/customer/billing/one-time/purchases/${purchaseId}/fulfillment`,
    )
  })
})
