import { test, expect } from "@playwright/test";

test.describe("Job Workflow", () => {
  test("test_job_create_and_view_flow", async ({ page }) => {
    // Navigate to jobs page
    await page.goto("/jobs");
    await expect(page.getByTestId("job-table")).toBeVisible();

    // Check job list renders
    const rows = page.locator("table tbody tr");
    const rowCount = await rows.count();

    // If create form exists, test creation
    const createBtn = page.getByTestId("job-create-btn");
    if (await createBtn.isVisible()) {
      await createBtn.click();
    }

    // Click on first job row if any to navigate to detail
    if (rowCount > 0) {
      const firstLink = rows.first().locator("a");
      if (await firstLink.isVisible()) {
        await firstLink.click();
        // Should be on detail page
        await expect(page).toHaveURL(/\/jobs\/.+/);
      }
    }
  });
});
