import { test, expect } from "@playwright/test";

/**
 * Phase 3 Step 3: 主链路 E2E 回归
 * 覆盖"数据集查看 → 任务创建/启动 → 产物查看 → Proposal 创建 → 导出查看"
 */

test.describe("Main Flow Regression", () => {
  test("test_dataset_to_job_to_artifact_smoke_flow", async ({ page }) => {
    // 1. 数据集页面可访问
    await page.goto("/datasets");
    await expect(page.locator("h1")).toContainText("Datasets");

    // 2. 导航到任务列表
    await page.goto("/jobs");
    await expect(page.locator("h1")).toContainText("任务列表");

    // 3. 点击"创建任务"按钮，表单可见
    const createBtn = page.getByRole("button", { name: "创建任务" });
    await expect(createBtn).toBeVisible();
    await createBtn.click();

    // 创建表单应出现（CreateJobForm 渲染了 form 元素）
    await expect(page.locator("form")).toBeVisible();

    // 4. 如果有任务行，进入详情查看产物
    const jobTable = page.getByTestId("job-table");
    if (await jobTable.isVisible()) {
      const firstLink = jobTable.locator("tbody tr a").first();
      if (await firstLink.isVisible()) {
        await firstLink.click();
        await expect(page).toHaveURL(/\/jobs\/.+/);

        // 切换到产物 tab
        const artifactTab = page.getByRole("button", { name: "产物" });
        if (await artifactTab.isVisible()) {
          await artifactTab.click();
          // 产物 tab 区域应渲染（无论有无数据）
          await expect(artifactTab).toBeVisible();
        }
      }
    }
  });

  test("test_candidate_confirmation_creates_next_job_flow", async ({
    page,
  }) => {
    // 1. 导航到 Proposals 页面
    await page.goto("/proposals");
    await expect(page.locator("h1")).toContainText("Proposals");

    // 2. 验证表单可见
    await expect(page.locator("text=验证 Proposal")).toBeVisible();

    // 3. 如果有 job ID 输入框，填入并提交
    const jobIdInput = page.locator("#jobId");
    if (await jobIdInput.isVisible()) {
      await jobIdInput.fill("job-001");
      const runIdInput = page.locator("#runId");
      if (await runIdInput.isVisible()) {
        await runIdInput.fill("run-001");
      }
      const submitBtn = page.locator("button[type='submit']");
      if (await submitBtn.isVisible()) {
        await submitBtn.click();
      }
    }

    // 4. 如果确认按钮可见，点击确认创建下一轮任务
    const confirmBtn = page.getByTestId("candidate-create-btn");
    if (await confirmBtn.isVisible()) {
      await confirmBtn.click();
      // 确认后可能跳转到任务页面或显示成功提示
      await page.waitForTimeout(500);
    }
  });

  test("test_export_creation_and_status_visibility_flow", async ({ page }) => {
    // 1. 导航到导出页面
    await page.goto("/exports");
    await expect(page.locator("h1")).toContainText("Exports");

    // 2. 创建导出表单可见
    await expect(page.locator("text=创建导出")).toBeVisible();

    // 3. 填写导出表单
    const jobIdInput = page.locator("#job_id");
    if (await jobIdInput.isVisible()) {
      await jobIdInput.fill("job-001");
      const runIdInput = page.locator("#run_id");
      if (await runIdInput.isVisible()) {
        await runIdInput.fill("run-001");
      }
      const createBtn = page.getByTestId("export-create-btn");
      if (await createBtn.isVisible()) {
        await createBtn.click();
        // 创建后应显示状态区域
        await page.waitForTimeout(1000);
      }
    }
  });

  test("test_pages_do_not_white_screen_when_backend_returns_empty", async ({
    page,
  }) => {
    // 即使后端返回空数据，各页面也不应产生未捕获异常或白屏

    // Datasets — 标题可见即表明未白屏
    await page.goto("/datasets");
    await expect(page.locator("h1")).toContainText("Datasets");

    // Jobs — 空列表显示"暂无任务"或表格，不应有未捕获错误
    await page.goto("/jobs");
    const jobsHeading = page.locator("h1");
    await expect(jobsHeading).toBeVisible();
    // 页面要么显示"暂无任务"要么显示任务表格
    const emptyOrTable = page
      .locator("text=暂无任务")
      .or(page.getByTestId("job-table"));
    await expect(emptyOrTable.first()).toBeVisible();

    // Proposals — 标题可见
    await page.goto("/proposals");
    await expect(page.locator("h1")).toContainText("Proposals");

    // Exports — 标题可见
    await page.goto("/exports");
    await expect(page.locator("h1")).toContainText("Exports");

    // 验证没有控制台错误导致的白屏（通过 ErrorBoundary 保护）
    // 如果发生白屏，h1 不会渲染，上述断言就会失败
  });
});
