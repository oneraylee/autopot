import { test, expect } from "@playwright/test";

test.describe("Smoke: Navigation", () => {
  test("homepage redirects to a dashboard page", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/\/(projects|datasets|jobs)/);
  });

  test("sidebar navigation links are visible", async ({ page }) => {
    await page.goto("/jobs");
    await expect(page.getByTestId("nav-projects")).toBeVisible();
    await expect(page.getByTestId("nav-datasets")).toBeVisible();
    await expect(page.getByTestId("nav-jobs")).toBeVisible();
    await expect(page.getByTestId("nav-proposals")).toBeVisible();
    await expect(page.getByTestId("nav-exports")).toBeVisible();
  });
});
