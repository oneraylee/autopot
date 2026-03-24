import { describe, it, expect } from "vitest";

describe("Phase6-Step1: 知识系统 Zod 校验 Schema", () => {
  // ──────────────────────────────────────────────────
  // source_type 枚举校验
  // ──────────────────────────────────────────────────
  it("test_source_type_enum_validation", async () => {
    const { createSourceSchema } = await import("@/schemas/knowledge");
    const invalid = {
      source_type: "invalid_type",
      name: "Test",
      uri: "/path",
      trust_level: 3,
    };
    expect(createSourceSchema.safeParse(invalid).success).toBe(false);
    const valid = {
      source_type: "local",
      name: "Test",
      uri: "/path",
      trust_level: 3,
    };
    expect(createSourceSchema.safeParse(valid).success).toBe(true);
  });

  it("test_all_source_type_values_accepted", async () => {
    const { createSourceSchema } = await import("@/schemas/knowledge");
    for (const t of ["local", "web", "official_doc", "internal_experiment"]) {
      const r = createSourceSchema.safeParse({
        source_type: t,
        name: "n",
        uri: t === "web" ? "https://example.com" : "/path",
        trust_level: 3,
      });
      expect(r.success).toBe(true);
    }
  });

  // ──────────────────────────────────────────────────
  // URL 格式校验（web 类型需要 URL 格式）
  // ──────────────────────────────────────────────────
  it("test_url_format_validation", async () => {
    const { createSourceSchema } = await import("@/schemas/knowledge");
    const invalidUrl = {
      source_type: "web",
      name: "Test",
      uri: "not-a-url",
      trust_level: 3,
    };
    expect(createSourceSchema.safeParse(invalidUrl).success).toBe(false);
    const validUrl = {
      source_type: "web",
      name: "Test",
      uri: "https://example.com/doc",
      trust_level: 3,
    };
    expect(createSourceSchema.safeParse(validUrl).success).toBe(true);
  });

  // ──────────────────────────────────────────────────
  // skill_code 格式校验（层级.类别.名称，不含空格或特殊字符）
  // ──────────────────────────────────────────────────
  it("test_skill_code_format_validation", async () => {
    const { createTechniqueSchema } = await import("@/schemas/knowledge");
    const invalid = {
      skill_code: "invalid code!",
      name: "Test",
      category: "training",
      layer: "augment",
      task_type: "det",
    };
    expect(createTechniqueSchema.safeParse(invalid).success).toBe(false);
    const valid = {
      skill_code: "train.augment.mosaic",
      name: "Mosaic",
      category: "training",
      layer: "augment",
      task_type: "det",
    };
    expect(createTechniqueSchema.safeParse(valid).success).toBe(true);
  });

  // ──────────────────────────────────────────────────
  // 必填字段校验
  // ──────────────────────────────────────────────────
  it("test_invalid_values_rejected", async () => {
    const { createSourceSchema } = await import("@/schemas/knowledge");
    expect(createSourceSchema.safeParse({}).success).toBe(false);
    expect(
      createSourceSchema.safeParse({ source_type: "local" }).success,
    ).toBe(false);
  });

  // ──────────────────────────────────────────────────
  // importDocumentSchema
  // ──────────────────────────────────────────────────
  it("test_import_document_schema_validation", async () => {
    const { importDocumentSchema } = await import("@/schemas/knowledge");
    expect(importDocumentSchema.safeParse({}).success).toBe(false);
    const valid = {
      source_id: "src-1",
      title: "Doc Title",
      doc_type: "markdown",
    };
    expect(importDocumentSchema.safeParse(valid).success).toBe(true);
  });

  it("test_doc_type_enum_validation", async () => {
    const { importDocumentSchema } = await import("@/schemas/knowledge");
    const invalid = {
      source_id: "src-1",
      title: "Title",
      doc_type: "unknown_type",
    };
    expect(importDocumentSchema.safeParse(invalid).success).toBe(false);
  });

  // ──────────────────────────────────────────────────
  // createTechniqueSchema
  // ──────────────────────────────────────────────────
  it("test_create_technique_schema_requires_fields", async () => {
    const { createTechniqueSchema } = await import("@/schemas/knowledge");
    expect(createTechniqueSchema.safeParse({}).success).toBe(false);
    const valid = {
      skill_code: "train.augment.mosaic",
      name: "Mosaic",
      category: "training",
      layer: "augment",
      task_type: "det",
    };
    expect(createTechniqueSchema.safeParse(valid).success).toBe(true);
  });

  it("test_category_enum_validation", async () => {
    const { createTechniqueSchema } = await import("@/schemas/knowledge");
    const invalid = {
      skill_code: "x.y.z",
      name: "X",
      category: "invalid_category",
      layer: "augment",
      task_type: "det",
    };
    expect(createTechniqueSchema.safeParse(invalid).success).toBe(false);
  });
});
