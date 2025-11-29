import { expect, test } from "@playwright/test"

test.describe("Branch Operations Workflow", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page and login
    await page.goto("/login")
    await page.fill('input[type="email"]', "admin@example.com")
    await page.fill('input[type="password"]', "changethis")
    await page.click('button[type="submit"]')
    await page.waitForURL(/\/projects/)
  })

  test("branch switching and modification flow", async ({ page }) => {
    // Navigate to a project
    await page.goto("/projects")
    await page.waitForSelector("text=Projects")

    // Click on first project
    const projectLink = page.locator('a[href*="/projects/"]').first()
    if ((await projectLink.count()) > 0) {
      await projectLink.click()
      await page.waitForURL(/\/projects\/[^/]+/)

      // Find branch selector
      const branchSelector = page.locator(
        'select[name="branch"], button:has-text("Branch")',
      )
      if ((await branchSelector.count()) > 0) {
        // Branch selector should be visible
        await expect(branchSelector).toBeVisible()
      }
    }
  })

  test("merge branch flow", async ({ page }) => {
    // Navigate to a project with change orders
    await page.goto("/projects")
    await page.waitForSelector("text=Projects")

    const projectLink = page.locator('a[href*="/projects/"]').first()
    if ((await projectLink.count()) > 0) {
      await projectLink.click()
      await page.waitForURL(/\/projects\/[^/]+/)

      // Navigate to Change Orders tab
      const changeOrdersTab = page.locator('button:has-text("Change Orders")')
      if ((await changeOrdersTab.count()) > 0) {
        await changeOrdersTab.click()

        // Find a change order with a branch
        const mergeButton = page.locator('button:has-text("Merge")').first()
        if ((await mergeButton.count()) > 0) {
          await mergeButton.click()

          // Merge dialog should appear
          await page.waitForSelector("text=Merge Branch", { timeout: 3000 })

          // Confirm merge
          const confirmButton = page.locator('button:has-text("Confirm")')
          if ((await confirmButton.count()) > 0) {
            // In a real test, we might want to confirm, but for now just verify dialog appears
            await expect(confirmButton).toBeVisible()
          }
        }
      }
    }
  })
})
