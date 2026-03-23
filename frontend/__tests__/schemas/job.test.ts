import { describe, it, expect } from "vitest";
import { createJobSchema } from "@/schemas/job";

describe("Job Schema", () => {
  it("test_job_schema_requires_gpu_count_positive", () => {
    const invalid = {
      task_type: "training",
      dataset_version_id: "dv-1",
      config: {},
      resources: { gpu_count: 0 },
    };
    expect(createJobSchema.safeParse(invalid).success).toBe(false);
  });

  it("test_job_schema_accepts_valid", () => {
    const valid = {
      task_type: "training",
      dataset_version_id: "dv-1",
      config: {},
      resources: { gpu_count: 1 },
    };
    expect(createJobSchema.safeParse(valid).success).toBe(true);
  });

  it("test_job_schema_requires_task_type", () => {
    const invalid = {
      dataset_version_id: "dv-1",
      config: {},
      resources: { gpu_count: 1 },
    };
    expect(createJobSchema.safeParse(invalid).success).toBe(false);
  });

  it("test_job_schema_requires_dataset_version_id", () => {
    const invalid = {
      task_type: "training",
      config: {},
      resources: { gpu_count: 1 },
    };
    expect(createJobSchema.safeParse(invalid).success).toBe(false);
  });
});
