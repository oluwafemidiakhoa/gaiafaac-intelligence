import { expect, test } from '@playwright/test'

const productRoutes = [
  ['/terminal', 'Terminal'],
  ['/decision-rooms', 'Rooms'],
  ['/live', 'Live'],
  ['/fiscal-pulse', 'Intelligence'],
  ['/sources', 'Evidence'],
  ['/review', 'Review'],
  ['/institutional', 'Institutions'],
  ['/pricing', 'Pricing'],
]

test.describe('Gaia Control Plane', () => {
  test('keeps the full product navigation visible on desktop', async ({
    page,
  }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' })

    const primaryNavigation = page.getByRole('navigation', {
      name: 'Primary product navigation',
    })

    await expect(primaryNavigation).toBeVisible()

    for (const [href, label] of productRoutes.slice(0, 7)) {
      await expect(
        primaryNavigation.getByRole('link', { name: label, exact: true }),
      ).toHaveAttribute('href', href)
    }

    await expect(
      page.getByRole('link', { name: 'Pricing' }).first(),
    ).toHaveAttribute('href', '/pricing')
    await expect(
      page.getByRole('link', { name: 'Account' }).first(),
    ).toHaveAttribute('href', '/account')

    await expect(page.locator('header')).toHaveCount(1)
  })

  for (const [path, label] of productRoutes) {
    test(`${label} route renders without a server failure`, async ({
      page,
    }) => {
      const response = await page.goto(path, { waitUntil: 'domcontentloaded' })

      expect(response, `${path} should return an HTTP response`).not.toBeNull()
      expect(
        response.status(),
        `${path} should not be a 5xx response`,
      ).toBeLessThan(500)
      await expect(page.locator('body')).toBeVisible()
      await expect(page.locator('header')).toHaveCount(1)
    })
  }

  test('Watch Contracts expose the operational monitoring and outbound delivery surface', async ({
    page,
  }) => {
    const response = await page.goto('/watch-contracts', {
      waitUntil: 'domcontentloaded',
    })
    expect(response).not.toBeNull()
    expect(response.status()).toBeLessThan(500)
    await expect(
      page.getByRole('heading', { name: 'Fiscal Watch Contracts' }),
    ).toBeVisible()
    await expect(
      page.getByText('Decision infrastructure · continuous monitoring'),
    ).toBeVisible()
    await expect(
      page.getByText(
        /auditable in-app, opted-in email and institutional webhook delivery/i,
      ),
    ).toBeVisible()
  })

  test('Decision Rooms present the institutional evidence-boundary and review workflow', async ({
    page,
  }) => {
    await page.goto('/decision-rooms', { waitUntil: 'domcontentloaded' })
    await expect(
      page.getByRole('heading', {
        name: 'Preserve what your institution knew when it made the decision.',
      }),
    ).toBeVisible()
    await expect(
      page.getByText('Institutional decision infrastructure'),
    ).toBeVisible()
    await expect(page.getByText('Institutional review queue')).toBeVisible()
    await expect(
      page.getByRole('heading', {
        name: 'Decisions reopened by governed change',
      }),
    ).toBeVisible()
  })

  test('Decision Review route fails closed for an unknown room', async ({
    page,
  }) => {
    const response = await page.goto(
      '/decision-rooms/00000000-0000-4000-8000-000000000001/review',
      { waitUntil: 'domcontentloaded' },
    )
    expect(response).not.toBeNull()
    expect(response.status()).toBeLessThan(500)
    await expect(
      page.getByRole('heading', {
        name: 'See what changed before the institution changes its decision.',
      }),
    ).toBeVisible()
    await expect(page.locator('header')).toHaveCount(1)
  })

  test('public Fiscal Receipt verifier fails closed for an unknown receipt', async ({
    page,
  }) => {
    const response = await page.goto(
      '/verify/00000000-0000-4000-8000-000000000001',
      { waitUntil: 'domcontentloaded' },
    )
    expect(response).not.toBeNull()
    expect(response.status()).toBeLessThan(500)
    await expect(
      page.getByRole('heading', { name: 'Receipt could not be verified' }),
    ).toBeVisible()
  })

  test('Review remains a first-class evidence-control surface', async ({
    page,
  }) => {
    await page.goto('/review', { waitUntil: 'domcontentloaded' })

    await expect(
      page.getByRole('heading', {
        name: 'Nothing gets published by accident.',
      }),
    ).toBeVisible()
    await expect(page.getByText('Four-eyes protocol')).toBeVisible()
    await expect(page.getByText('Evidence lanes')).toBeVisible()
  })

  test('Intelligence remains reachable from the primary navigation', async ({
    page,
  }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' })

    const intelligenceLink = page
      .getByRole('navigation', { name: 'Primary product navigation' })
      .getByRole('link', { name: 'Intelligence', exact: true })

    await intelligenceLink.click()
    await expect(page).toHaveURL(/\/fiscal-pulse(?:\?|$)/)
    await expect(page.locator('h1').first()).toBeVisible()
  })

  test('critical desktop surfaces do not overflow horizontally', async ({
    page,
  }) => {
    for (const path of [
      '/',
      '/terminal',
      '/decision-rooms',
      '/watch-contracts',
      '/fiscal-pulse',
      '/review',
      '/pricing',
    ]) {
      await page.goto(path, { waitUntil: 'domcontentloaded' })
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - window.innerWidth,
      )
      expect(overflow, `${path} has horizontal overflow`).toBeLessThanOrEqual(2)
    }
  })
})

test.describe('Gaia Control Plane mobile navigation', () => {
  test.use({
    viewport: { width: 390, height: 844 },
    hasTouch: true,
    isMobile: true,
  })

  test('mobile menu preserves product and commercial navigation', async ({
    page,
  }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' })
    await page.getByText('Menu', { exact: true }).click()

    const mobileNavigation = page.getByRole('navigation', {
      name: 'Mobile product navigation',
    })

    await expect(mobileNavigation).toBeVisible()
    await expect(
      mobileNavigation.getByRole('link', { name: 'Terminal', exact: true }),
    ).toBeVisible()
    await expect(
      mobileNavigation.getByRole('link', {
        name: 'Decision Rooms',
        exact: true,
      }),
    ).toBeVisible()
    for (const label of [
      'Live',
      'Intelligence',
      'Evidence',
      'Review',
      'Institutions',
    ]) {
      await expect(
        mobileNavigation.getByRole('link', { name: label, exact: true }),
      ).toBeVisible()
    }

    await expect(
      page.getByRole('link', { name: 'Pricing', exact: true }).first(),
    ).toBeVisible()
    await expect(
      page.getByRole('link', { name: 'Account', exact: true }).first(),
    ).toBeVisible()
  })
})
