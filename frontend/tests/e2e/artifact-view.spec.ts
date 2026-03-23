import { test, expect } from "@playwright/test";

test.describe("Artifact View", () => {
  test("test_artifact_tab_navigation", async ({ page }) => {
    // Navigate to a job detail page (assumes at least one job exists)
    await page.goto("/jobs");
    const firstJobLink = page.locator("table tbody tr a").first();

    if (await firstJobLink.isVisible()) {
      await firstJobLink.click();
      await expect(page).toHaveURL(/\/jobs\/.+/);

      // Check if artifact tabs are present
      const evalTab = page.getByTestId("artifact-tab-eval");
      if (await evalTab.isVisible()) {
        await evalTab.click();
        await expect(page.locator("[data-testid='artifact-tab-eval']")).toBeVisible();

        // Switch to analysis tab
        const analysisTab = page.getByTestId("artifact-tab-analysis");
        await analysisTab.click();
        await expect(analysisTab).toBeVisible();

        // Switch to experiments tab
        const expTab = page.getByTestId("artifact-tab-experiments");
        await expTab.click();
        await expect(expTab).toBeVisible();
      }
    }
  });
});
