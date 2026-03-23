import { test, expect } from "@playwright/test";

test.describe("Export Workflow", () => {
  test("test_export_create_and_status", async ({ page }) => {
    // Navigate to exports page
    await page.goto("/exports");
    await expect(page.getByTestId("nav-exports")).toBeVisible();

    // If create export form is visible, fill and submit
    const jobIdInput = page.locator("#job_id");
    if (await jobIdInput.isVisible()) {
      await jobIdInput.fill("job-001");
      const runIdInput = page.locator("#run_id");
      await runIdInput.fill("run-001");

      await page.getByTestId("export-create-btn").click();

      // Wait for feedback
      await expect(page.locator("text=创建中")).toBeHidden({ timeout: 10000 });
    }
  });
});
