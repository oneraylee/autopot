import { test, expect } from "@playwright/test";

test.describe("Knowledge Review Workflow", () => {
  test("test_e2e_skill_review_workflow", async ({ page }) => {
    const createdSkills: Array<{ name: string }> = [];

    await page.route("**://localhost:8000/knowledge/techniques**", async (route, request) => {
      const url = new URL(request.url());

      if (url.pathname === "/knowledge/techniques/extract") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            ok: true,
            data: {
              candidates: [
                {
                  candidate_id: "cand-1",
                  name: "Cosine LR",
                  category: "training",
                  layer: "schedule",
                  condition: "训练后期",
                  action: "使用余弦退火",
                  tradeoff: "收敛稳定",
                },
              ],
            },
          }),
        });
        return;
      }

      if (url.pathname === "/knowledge/techniques" && request.method() === "POST") {
        const body = request.postDataJSON() as { name: string };
        createdSkills.push({ name: body.name });
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            ok: true,
            data: {
              technique_id: "tech-created",
              skill_code: "training.schedule.cosine_lr",
              name: body.name,
              category: "training",
              layer: "schedule",
              task_type: "det",
              maturity: "draft",
              status: "active",
            },
          }),
        });
        return;
      }

      if (url.pathname === "/knowledge/techniques" && request.method() === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            ok: true,
            data: {
              items: createdSkills.map((item, idx) => ({
                technique_id: `tech-${idx + 1}`,
                skill_code: "training.schedule.cosine_lr",
                name: item.name,
                category: "training",
                layer: "schedule",
                task_type: "det",
                maturity: "draft",
                status: "active",
              })),
              total: createdSkills.length,
            },
          }),
        });
        return;
      }

      await route.continue();
    });

    await page.goto("/knowledge/review?doc_id=doc-review-1");
    await expect(page.getByTestId("skill-extract-review")).toBeVisible();
    await page.getByTestId("extract-skills-btn").click();
    await expect(page.getByTestId("candidate-item")).toBeVisible();
    await page.getByTestId("candidate-confirm-btn-cand-1").click();

    await page.goto("/knowledge/skills");
    await expect(page.getByTestId("skill-list")).toBeVisible();
    await expect(page.getByTestId("skill-row-tech-1")).toBeVisible();
  });
});
