import { expect, test } from "@playwright/test"

test.describe("Cost Performance Report", () => {
  test("should navigate to cost performance report from project metrics tab", async ({
    page,
  }) => {
    // Navigate to first project
    await page.goto("/projects")
    await page.waitForSelector("table")
    const firstProjectLink = page.locator("table tbody tr").first()
    const _projectId = await firstProjectLink
      .locator("td")
      .first()
      .textContent()
    await firstProjectLink.click()

    // Wait for project detail page
    await page.waitForURL(/\/projects\/[^/]+$/)

    // Click on Metrics tab
    await page.click('button:has-text("Metrics")')

    // Click on "View Cost Performance Report" link
    await page.click('text="View Cost Performance Report"')

    // Wait for report page to load
    await page.waitForURL(/\/projects\/[^/]+\/reports\/cost-performance/)

    // Verify report is displayed
    await expect(page.locator("text=Cost Performance Report")).toBeVisible()
  })

  test("should display report data in table", async ({ page }) => {
    // Navigate directly to a project's report (assuming project exists)
    await page.goto("/projects")
    await page.waitForSelector("table")
    const firstProjectLink = page.locator("table tbody tr").first()
    await firstProjectLink.click()

    // Wait for project detail page
    await page.waitForURL(/\/projects\/[^/]+$/)

    // Navigate to report
    const projectUrl = page.url()
    const projectId = projectUrl.split("/projects/")[1].split("/")[0]
    await page.goto(`/projects/${projectId}/reports/cost-performance`)

    // Wait for report to load
    await page.waitForSelector("text=Cost Performance Report")

    // Verify table is present (may be empty)
    const table = page.locator("table").first()
    await expect(table).toBeVisible()

    // Verify summary section is present
    await expect(page.locator("text=Project Summary")).toBeVisible()
  })

  test("should handle empty report gracefully", async ({ page }) => {
    // Create a new project without cost elements
    await page.goto("/projects")
    await page.click('button:has-text("New Project")')
    await page.fill('input[name="project_name"]', "Empty Test Project")
    await page.fill('input[name="customer_name"]', "Test Customer")
    await page.fill('input[name="contract_value"]', "100000")
    await page.fill('input[name="start_date"]', "2024-01-01")
    await page.fill('input[name="planned_completion_date"]', "2024-12-31")
    await page.click('button[type="submit"]')

    // Wait for project to be created and navigate to it
    await page.waitForURL(/\/projects\/[^/]+$/)
    const projectUrl = page.url()
    const projectId = projectUrl.split("/projects/")[1].split("/")[0]

    // Navigate to report
    await page.goto(`/projects/${projectId}/reports/cost-performance`)

    // Verify empty state message
    await expect(
      page.locator("text=No cost elements found for this project"),
    ).toBeVisible()
  })
})
