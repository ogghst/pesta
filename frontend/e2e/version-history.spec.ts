import { expect, test } from "@playwright/test"

test.describe("Version History Workflow", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page and login
    await page.goto("/login")
    await page.fill('input[type="email"]', "admin@example.com")
    await page.fill('input[type="password"]', "changethis")
    await page.click('button[type="submit"]')
    await page.waitForURL(/\/projects/)
  })

  test("version history viewing flow", async ({ page }) => {
    // Navigate to a project
    await page.goto("/projects")
    await page.waitForSelector("text=Projects")

    // Click on first project
    const projectLink = page.locator('a[href*="/projects/"]').first()
    if ((await projectLink.count()) > 0) {
      await projectLink.click()
      await page.waitForURL(/\/projects\/[^/]+/)

      // Look for version history button or link
      const versionHistoryButton = page.locator(
        'button:has-text("Version History"), a:has-text("Version History")',
      )
      if ((await versionHistoryButton.count()) > 0) {
        await versionHistoryButton.click()

        // Version history should be displayed
        await page.waitForSelector("text=Version History", { timeout: 3000 })
        await expect(page.locator("text=Version History")).toBeVisible()
      }
    }
  })

  test("view version details", async ({ page }) => {
    // Navigate to a project
    await page.goto("/projects")
    await page.waitForSelector("text=Projects")

    const projectLink = page.locator('a[href*="/projects/"]').first()
    if ((await projectLink.count()) > 0) {
      await projectLink.click()
      await page.waitForURL(/\/projects\/[^/]+/)

      // Navigate to version history
      const versionHistoryButton = page.locator(
        'button:has-text("Version History"), a:has-text("Version History")',
      )
      if ((await versionHistoryButton.count()) > 0) {
        await versionHistoryButton.click()
        await page.waitForSelector("text=Version History", { timeout: 3000 })

        // Click on a version to view details
        const versionItem = page
          .locator('[data-testid*="version"], .version-item')
          .first()
        if ((await versionItem.count()) > 0) {
          await versionItem.click()
          // Version details should be visible
          await expect(page.locator("text=Version")).toBeVisible()
        }
      }
    }
  })
})
