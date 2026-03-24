import { test, expect } from "@playwright/test";

test.describe("Gateway View Workflow", () => {
  test("test_e2e_gateway_view_workflow", async ({ page }) => {
    await page.route("**/llm-gateway/providers", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          ok: true,
          data: [
            { name: "openai", models: ["gpt-4o", "gpt-4o-mini"], status: "active" },
          ],
        }),
      });
    });

    await page.route("**/llm-gateway/usage**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          ok: true,
          data: {
            items: [
              { date: "2026-03-20", provider: "openai", tokens: 12000, cost: 1.2 },
            ],
            total_tokens: 12000,
            total_cost: 1.2,
          },
        }),
      });
    });

    await page.route("**/llm-gateway/call-logs**", async (route, request) => {
      const url = new URL(request.url());
      const pageNum = Number(url.searchParams.get("page") ?? "1");
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          ok: true,
          data: {
            items: [
              {
                id: `log-${pageNum}`,
                call_type: "agent_plan",
                provider: "openai",
                model: "gpt-4o",
                input_tokens: 500,
                output_tokens: 300,
                latency_ms: 800,
                cost: 0.02,
                status: "success",
                created_at: "2026-03-20T10:00:00Z",
              },
            ],
            page: pageNum,
            page_size: 20,
            total: 40,
          },
        }),
      });
    });

    await page.goto("/jobs");
    await expect(page.getByTestId("nav-settings")).toBeVisible();
    await page.getByTestId("nav-settings").click();

    await expect(page).toHaveURL(/\/settings\/llm-gateway/);
    await expect(page.getByTestId("provider-list")).toBeVisible();

    await page.getByTestId("usage-start-date").fill("2026-03-01");
    await page.getByTestId("usage-end-date").fill("2026-03-31");
    await page.getByTestId("group-by-model").click();
    await expect(page.getByTestId("usage-chart")).toBeVisible();

    await page.getByTestId("filter-call-type").selectOption("agent_plan");
    await page.getByTestId("filter-provider").selectOption("openai");
    await page.getByTestId("filter-status").selectOption("success");
    await page.getByTestId("call-log-next-page").click();
    await expect(page.getByText("第 2 / 2 页")).toBeVisible();
  });
});
