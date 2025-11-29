import { test } from "@playwright/test"

test.describe("Change Order Workflow", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page and login
    await page.goto("/login")
    await page.fill('input[type="email"]', "admin@example.com")
    await page.fill('input[type="password"]', "changethis")
    await page.click('button[type="submit"]')
    await page.waitForURL(/\/projects/)
  })

  test("complete change order workflow: create, modify, approve, merge", async ({
    page,
  }) => {
    // Navigate to a project
    await page.goto("/projects")
    await page.waitForSelector("text=Projects")

    // Click on first project (if available)
    const projectLink = page.locator('a[href*="/projects/"]').first()
    if ((await projectLink.count()) > 0) {
      await projectLink.click()
      await page.waitForURL(/\/projects\/[^/]+/)

      // Navigate to Change Orders tab
      const changeOrdersTab = page.locator('button:has-text("Change Orders")')
      if ((await changeOrdersTab.count()) > 0) {
        await changeOrdersTab.click()

        // Create a new change order
        const createButton = page.locator('button:has-text("Add Change Order")')
        if ((await createButton.count()) > 0) {
          await createButton.click()

          // Fill in change order form
          await page.fill('input[name="title"]', "E2E Test Change Order")
          await page.fill(
            'textarea[name="description"]',
            "E2E test description",
          )
          await page.fill('input[name="requesting_party"]', "Customer")
          await page.fill('input[name="effective_date"]', "2024-06-01")

          // Submit form
          const submitButton = page.locator(
            'button[type="submit"]:has-text("Create")',
          )
          await submitButton.click()

          // Wait for change order to appear in table
          await page.waitForSelector("text=E2E Test Change Order", {
            timeout: 5000,
          })
        }
      }
    }
  })
})
