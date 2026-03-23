import { describe, it, expect } from "vitest";
import { createExportSchema } from "@/schemas/export";

describe("Export Schema", () => {
  it("test_export_schema_limits_backend_enum", () => {
    const invalid = {
      job_id: "j-1",
      run_id: "r-1",
      backend: "invalid_backend",
    };
    expect(createExportSchema.safeParse(invalid).success).toBe(false);
  });

  it("test_export_schema_accepts_tensorrt", () => {
    const valid = {
      job_id: "j-1",
      run_id: "r-1",
      backend: "tensorrt",
    };
    expect(createExportSchema.safeParse(valid).success).toBe(true);
  });

  it("test_export_schema_requires_all_fields", () => {
    expect(createExportSchema.safeParse({}).success).toBe(false);
    expect(createExportSchema.safeParse({ job_id: "j-1" }).success).toBe(false);
    expect(createExportSchema.safeParse({ job_id: "j-1", run_id: "r-1" }).success).toBe(false);
  });
});
