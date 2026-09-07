import { expect, test } from '@playwright/test'

test('Decision Packet visual evidence QA', async ({ page }, testInfo) => {
  await page.goto('/decision-packets/lagos?year=2026')
  await expect(
    page.getByRole('heading', {
      name: 'What the governed evidence says now',
    }),
  ).toBeVisible()
  const chart = page.getByTestId('fiscal-flow-chart')
  await expect(chart).toBeVisible()
  const bars = chart.getByTestId('fiscal-bar')
  expect(await bars.count()).toBeGreaterThan(0)
  const box = await bars.first().boundingBox()
  expect(box?.height).toBeGreaterThan(0)
  expect(box?.width).toBeGreaterThan(0)
  const january = page.getByRole('link', { name: 'Jan 2026 fiscal proof' })
  await expect(january).toHaveAttribute(
    'href',
    '/fiscal-proof/lagos/2026-01-01',
  )
  const details = page.locator('details').filter({ hasText: 'Jan 2026 / Net' })
  await details.locator('summary').click()
  await expect(details).toContainText('Arithmetic residual')
  await expect(details).toContainText('SHA-256')
  await expect(details.getByRole('link')).toHaveAttribute(
    'href',
    '/fiscal-proof/lagos/2026-01-01',
  )
  await testInfo.attach('desktop-fiscal-chart', {
    body: await chart.screenshot(),
    contentType: 'image/png',
  })
  await testInfo.attach('desktop-evidence-details', {
    body: await details.screenshot(),
    contentType: 'image/png',
  })
  await page.setViewportSize({ width: 390, height: 844 })
  await expect(details).toBeVisible()
  const pageWidth = await page.evaluate(
    () => document.documentElement.scrollWidth,
  )
  expect(pageWidth).toBeLessThanOrEqual(390)
  await testInfo.attach('mobile-evidence-details', {
    body: await details.screenshot(),
    contentType: 'image/png',
  })
})
