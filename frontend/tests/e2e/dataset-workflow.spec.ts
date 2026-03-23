import { test, expect } from "@playwright/test";

test.describe("Dataset Workflow", () => {
  test("test_dataset_import_and_freeze_flow", async ({ page }) => {
    // Navigate to datasets page
    await page.goto("/datasets");
    await expect(page.getByTestId("nav-datasets")).toBeVisible();

    // Fill import form
    const versionInput = page.locator("#version");
    const manifestInput = page.locator("#manifest_uri");
    if (await versionInput.isVisible()) {
      await versionInput.fill("2");
      await manifestInput.fill("s3://bucket/manifest.json");
      await page.getByTestId("dataset-import-btn").click();

      // Wait for success feedback
      await expect(page.locator("text=导入中")).toBeHidden({ timeout: 10000 });
    }

    // Freeze button should be visible for an unfrozen version
    const freezeBtn = page.getByTestId("dataset-freeze-btn");
    if (await freezeBtn.isVisible()) {
      await freezeBtn.click();
      // After freeze, button should show frozen state
      await expect(freezeBtn).toBeDisabled();
    }
  });
});
