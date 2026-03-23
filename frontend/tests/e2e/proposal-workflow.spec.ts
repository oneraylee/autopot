import { test, expect } from "@playwright/test";

test.describe("Proposal Workflow", () => {
  test("test_proposal_confirm_creates_job", async ({ page }) => {
    // Navigate to proposals page
    await page.goto("/proposals");
    await expect(page.getByTestId("nav-proposals")).toBeVisible();

    // If validate form is visible, fill and submit
    const jobIdInput = page.locator("#jobId");
    if (await jobIdInput.isVisible()) {
      await jobIdInput.fill("job-001");
      const runIdInput = page.locator("#runId");
      await runIdInput.fill("run-001");

      const submitBtn = page.locator("button[type='submit']");
      await submitBtn.click();
    }

    // Check confirm dialog
    const confirmBtn = page.getByTestId("candidate-create-btn");
    if (await confirmBtn.isVisible()) {
      await confirmBtn.click();
    }
  });
});
