import { describe, it, expect, vi, beforeEach } from "vitest";

describe("Phase2-Step1: 项目 API Client 与 KPI 配置", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.resetModules();
  });

  it("test_get_kpi_config_returns_valid_structure", async () => {
    const mockKpi = {
      primary_kpi: "mAP",
      threshold: 0.75,
      weights: { eval: 0.6, deploy: 0.4 },
      deploy_constraints: [{ metric: "latency_ms", operator: "<=", value: 50 }],
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ok: true, data: mockKpi }),
      }),
    );
    const { getKpiConfig } = await import("@/lib/api/project");
    const result = await getKpiConfig("proj-1");
    expect(result).toEqual(mockKpi);
    expect(result.primary_kpi).toBe("mAP");
    expect(result.weights.eval).toBe(0.6);
    expect(result.deploy_constraints).toHaveLength(1);
  });

  it("test_get_kpi_config_not_found_throws_api_error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            ok: false,
            error: {
              code: "NOT_FOUND",
              message: "Project not found",
              details: [],
              type: "business_error",
            },
          }),
      }),
    );
    const { getKpiConfig } = await import("@/lib/api/project");
    const { ApiError } = await import("@/lib/api/errors");
    await expect(getKpiConfig("proj-999")).rejects.toThrow(ApiError);
  });

  it("test_get_kpi_config_calls_correct_endpoint", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            ok: true,
            data: {
              primary_kpi: "mAP",
              threshold: 0.5,
              weights: { eval: 0.5, deploy: 0.5 },
              deploy_constraints: [],
            },
          }),
      }),
    );
    const { getKpiConfig } = await import("@/lib/api/project");
    await getKpiConfig("proj-1");
    expect(vi.mocked(fetch)).toHaveBeenCalledWith(
      expect.stringContaining("/projects/proj-1/kpi-config"),
      expect.any(Object),
    );
  });

  it("test_kpi_config_hook_exists", async () => {
    const mod = await import("@/features/project/hooks/useKpiConfig");
    expect(mod.useKpiConfig).toBeDefined();
  });

  it("test_kpi_config_page_exists", async () => {
    const fs = await import("fs");
    const path = await import("path");
    const pagePath = path.resolve(
      __dirname,
      "../../../src/app/(dashboard)/projects/[id]/kpi-config/page.tsx",
    );
    expect(fs.existsSync(pagePath)).toBe(true);
  });
});
