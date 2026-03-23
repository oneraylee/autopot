import { describe, it, expect } from "vitest";
import { datasetImportSchema, sceneLabelSchema } from "@/schemas/dataset";

describe("Dataset Import Schema", () => {
  it("test_dataset_import_schema_requires_version_positive_int", () => {
    expect(datasetImportSchema.safeParse({ version: 0, manifest_uri: "s3://a" }).success).toBe(false);
    expect(datasetImportSchema.safeParse({ version: -1, manifest_uri: "s3://a" }).success).toBe(false);
    expect(datasetImportSchema.safeParse({ version: 1.5, manifest_uri: "s3://a" }).success).toBe(false);
  });

  it("test_dataset_import_schema_accepts_valid", () => {
    expect(datasetImportSchema.safeParse({ version: 1, manifest_uri: "s3://bucket/data" }).success).toBe(true);
  });

  it("test_dataset_import_schema_rejects_empty_uri", () => {
    expect(datasetImportSchema.safeParse({ version: 1, manifest_uri: "" }).success).toBe(false);
  });
});

describe("Scene Label Schema", () => {
  it("test_scene_label_schema_requires_other_text_when_weather_other", () => {
    const invalid = { frame_id: "f1", weather: "other" };
    expect(sceneLabelSchema.safeParse(invalid).success).toBe(false);
  });

  it("test_scene_label_schema_accepts_weather_other_with_text", () => {
    const valid = { frame_id: "f1", weather: "other", weather_other_text: "haze" };
    expect(sceneLabelSchema.safeParse(valid).success).toBe(true);
  });

  it("test_scene_label_schema_accepts_normal_weather", () => {
    const valid = { frame_id: "f1", weather: "clear" };
    expect(sceneLabelSchema.safeParse(valid).success).toBe(true);
  });
});
