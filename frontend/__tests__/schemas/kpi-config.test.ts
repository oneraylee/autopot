import { describe, it, expect } from "vitest";
import { kpiConfigSchema } from "@/schemas/kpi-config";

describe("KPI Config Schema", () => {
  it("test_kpi_schema_rejects_invalid_weight_sum", () => {
    const invalid = {
      primary_kpi: "漏检率",
      threshold: 0.05,
      weights: { eval: 0.7, deploy: 0.4 },
      deploy_constraints: [],
    };
    expect(kpiConfigSchema.safeParse(invalid).success).toBe(false);
  });

  it("test_kpi_schema_accepts_valid_config", () => {
    const valid = {
      primary_kpi: "漏检率",
      threshold: 0.05,
      weights: { eval: 0.5, deploy: 0.5 },
      deploy_constraints: [],
    };
    expect(kpiConfigSchema.safeParse(valid).success).toBe(true);
  });

  it("test_kpi_schema_rejects_threshold_out_of_range", () => {
    const invalid = {
      primary_kpi: "漏检率",
      threshold: 2,
      weights: { eval: 0.5, deploy: 0.5 },
      deploy_constraints: [],
    };
    expect(kpiConfigSchema.safeParse(invalid).success).toBe(false);
  });

  it("test_kpi_schema_rejects_negative_threshold", () => {
    const invalid = {
      primary_kpi: "漏检率",
      threshold: -0.1,
      weights: { eval: 0.5, deploy: 0.5 },
      deploy_constraints: [],
    };
    expect(kpiConfigSchema.safeParse(invalid).success).toBe(false);
  });
});
