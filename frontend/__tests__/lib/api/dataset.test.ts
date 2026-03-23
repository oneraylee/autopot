import { describe, it, expect, vi, beforeEach } from "vitest";
import fs from "fs";
import path from "path";

const root = path.resolve(__dirname, "../../..");

describe("Phase2-Step2: 数据集 API Client 与列表/详情", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.resetModules();
  });

  it("test_dataset_api_module_exports", async () => {
    const mod = await import("@/lib/api/dataset");
    expect(mod.importDatasetVersion).toBeDefined();
    expect(mod.freezeDatasetVersion).toBeDefined();
    expect(mod.upsertSceneLabels).toBeDefined();
    expect(mod.getSceneCoverage).toBeDefined();
  });

  it("test_get_scene_coverage_returns_dimension_stats", async () => {
    const mockCoverage = {
      dimensions: { weather: { clear: 100, rain: 50 }, time_of_day: { day: 80, night: 70 } },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ok: true, data: mockCoverage }),
      }),
    );
    const { getSceneCoverage } = await import("@/lib/api/dataset");
    const result = await getSceneCoverage("dv-1", ["weather", "time_of_day"]);
    expect(result.dimensions).toHaveProperty("weather");
    expect(result.dimensions).toHaveProperty("time_of_day");
  });

  it("test_get_scene_coverage_calls_correct_endpoint", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ok: true, data: { dimensions: {} } }),
      }),
    );
    const { getSceneCoverage } = await import("@/lib/api/dataset");
    await getSceneCoverage("dv-1", ["weather"]);
    expect(vi.mocked(fetch)).toHaveBeenCalledWith(
      expect.stringContaining("/datasets/versions/dv-1/scene-coverage"),
      expect.any(Object),
    );
  });

  it("test_dataset_hooks_exist", async () => {
    const mod = await import("@/features/dataset/hooks/useDatasetList");
    expect(mod.useDatasetList).toBeDefined();
  });

  it("test_dataset_list_page_exists", () => {
    expect(
      fs.existsSync(
        path.join(root, "src/app/(dashboard)/datasets/page.tsx"),
      ),
    ).toBe(true);
  });

  it("test_dataset_detail_page_exists", () => {
    expect(
      fs.existsSync(
        path.join(root, "src/app/(dashboard)/datasets/[id]/page.tsx"),
      ),
    ).toBe(true);
  });
});
