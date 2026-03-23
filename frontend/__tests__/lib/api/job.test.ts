import { describe, it, expect, vi, beforeEach } from "vitest";
import fs from "fs";
import path from "path";

const root = path.resolve(__dirname, "../../..");

describe("Phase2-Step3: 任务 API Client 与列表/详情", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.resetModules();
  });

  it("test_job_api_module_exports", async () => {
    const mod = await import("@/lib/api/job");
    expect(mod.getJob).toBeDefined();
    expect(mod.getJobLogs).toBeDefined();
    expect(mod.getJobMetrics).toBeDefined();
  });

  it("test_get_job_returns_status_and_type", async () => {
    const mockJob = {
      job_id: "j-1",
      task_type: "training",
      status: "running",
      dataset_version_id: "dv-1",
      created_at: "2025-01-01T00:00:00Z",
      updated_at: "2025-01-01T01:00:00Z",
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ok: true, data: mockJob }),
      }),
    );
    const { getJob } = await import("@/lib/api/job");
    const result = await getJob("j-1");
    expect(result.status).toBe("running");
    expect(result.task_type).toBe("training");
  });

  it("test_get_logs_supports_pagination", async () => {
    const mockLogs = {
      items: [{ line: 1, message: "start" }],
      page: 1,
      page_size: 20,
      total: 1,
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ok: true, data: mockLogs }),
      }),
    );
    const { getJobLogs } = await import("@/lib/api/job");
    const result = await getJobLogs("j-1", 1, 20);
    expect(vi.mocked(fetch)).toHaveBeenCalledWith(
      expect.stringContaining("page=1"),
      expect.any(Object),
    );
    expect(result.items).toHaveLength(1);
    expect(result.total).toBe(1);
  });

  it("test_get_metrics_supports_time_window", async () => {
    const mockMetrics = {
      items: [{ ts: 100, values: { loss: 0.5 } }],
      window: { start_ts: 0, end_ts: 200 },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ok: true, data: mockMetrics }),
      }),
    );
    const { getJobMetrics } = await import("@/lib/api/job");
    const result = await getJobMetrics("j-1", 0, 200);
    expect(vi.mocked(fetch)).toHaveBeenCalledWith(
      expect.stringContaining("start_ts=0"),
      expect.any(Object),
    );
    expect(result.items).toHaveLength(1);
  });

  it("test_job_hooks_exist", async () => {
    const mod = await import("@/features/job/hooks/useJobList");
    expect(mod.useJobList).toBeDefined();
  });

  it("test_job_list_page_exists", () => {
    expect(
      fs.existsSync(path.join(root, "src/app/(dashboard)/jobs/page.tsx")),
    ).toBe(true);
  });

  it("test_job_detail_page_exists", () => {
    expect(
      fs.existsSync(path.join(root, "src/app/(dashboard)/jobs/[id]/page.tsx")),
    ).toBe(true);
  });

  it("test_log_viewer_component_exists", () => {
    expect(
      fs.existsSync(
        path.join(root, "src/features/job/components/LogViewer.tsx"),
      ),
    ).toBe(true);
  });

  it("test_metrics_chart_component_exists", () => {
    expect(
      fs.existsSync(
        path.join(root, "src/features/job/components/MetricsChart.tsx"),
      ),
    ).toBe(true);
  });
});
