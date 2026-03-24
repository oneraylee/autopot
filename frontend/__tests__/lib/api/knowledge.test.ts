import { describe, it, expect, vi, beforeEach } from "vitest";
import fs from "fs";
import path from "path";

const root = path.resolve(__dirname, "../../..");

describe("Phase6-Step1: 知识系统 API Client (KnowledgeClientGate)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.resetModules();
  });

  // ──────────────────────────────────────────────────
  // 文件存在性
  // ──────────────────────────────────────────────────
  it("test_knowledge_api_file_exists", () => {
    const p = path.join(root, "src/lib/api/knowledge.ts");
    expect(fs.existsSync(p)).toBe(true);
  });

  it("test_knowledge_types_file_exists", () => {
    const p = path.join(root, "src/features/knowledge/types.ts");
    expect(fs.existsSync(p)).toBe(true);
  });

  // ──────────────────────────────────────────────────
  // API 方法存在性
  // ──────────────────────────────────────────────────
  it("test_types_align_with_backend", async () => {
    const { knowledgeApi } = await import("@/lib/api/knowledge");
    expect(typeof knowledgeApi.createSource).toBe("function");
    expect(typeof knowledgeApi.listSources).toBe("function");
    expect(typeof knowledgeApi.importDocument).toBe("function");
    expect(typeof knowledgeApi.getDocument).toBe("function");
    expect(typeof knowledgeApi.getChunks).toBe("function");
    expect(typeof knowledgeApi.extractSkills).toBe("function");
    expect(typeof knowledgeApi.extractTechniques).toBe("function");
    expect(typeof knowledgeApi.createTechnique).toBe("function");
    expect(typeof knowledgeApi.updateTechnique).toBe("function");
    expect(typeof knowledgeApi.listTechniques).toBe("function");
    expect(typeof knowledgeApi.getTechnique).toBe("function");
    expect(typeof knowledgeApi.publishTechnique).toBe("function");
    expect(typeof knowledgeApi.resolveConflicts).toBe("function");
  });

  // ──────────────────────────────────────────────────
  // createSource
  // ──────────────────────────────────────────────────
  it("test_createSource_returns_source_id", async () => {
    const mockSource = {
      source_id: "src-1",
      source_type: "local",
      name: "YOLO 改造资料",
      uri: "/docs/yolo.md",
      trust_level: 3,
      status: "active",
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ok: true, data: mockSource }),
      }),
    );
    const { knowledgeApi } = await import("@/lib/api/knowledge");
    const result = await knowledgeApi.createSource({
      source_type: "local",
      name: "YOLO 改造资料",
      uri: "/docs/yolo.md",
      trust_level: 3,
    });
    expect(result.source_id).toBe("src-1");
    expect(result.source_type).toBe("local");
  });

  it("test_createSource_calls_correct_endpoint", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            ok: true,
            data: {
              source_id: "s-1",
              source_type: "local",
              name: "n",
              uri: "u",
              trust_level: 1,
              status: "active",
            },
          }),
      }),
    );
    const { knowledgeApi } = await import("@/lib/api/knowledge");
    await knowledgeApi.createSource({
      source_type: "local",
      name: "n",
      uri: "u",
      trust_level: 1,
    });
    expect(vi.mocked(fetch)).toHaveBeenCalledWith(
      expect.stringContaining("/knowledge/sources"),
      expect.any(Object),
    );
  });

  // ──────────────────────────────────────────────────
  // importDocument
  // ──────────────────────────────────────────────────
  it("test_importDocument_returns_document_id", async () => {
    const mockDoc = {
      document_id: "doc-1",
      source_id: "src-1",
      title: "YOLO 实战指南",
      doc_type: "markdown",
      parse_status: "pending",
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ok: true, data: mockDoc }),
      }),
    );
    const { knowledgeApi } = await import("@/lib/api/knowledge");
    const result = await knowledgeApi.importDocument({
      source_id: "src-1",
      title: "YOLO 实战指南",
      doc_type: "markdown",
    });
    expect(result.document_id).toBe("doc-1");
    expect(result.parse_status).toBe("pending");
  });

  // ──────────────────────────────────────────────────
  // listTechniques
  // ──────────────────────────────────────────────────
  it("test_listTechniques_supports_filters", async () => {
    const mockList = {
      techniques: [
        {
          technique_id: "t-1",
          name: "Mosaic数据增强",
          category: "training",
          layer: "augment",
          status: "active",
          maturity: "verified",
        },
      ],
      total: 1,
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ok: true, data: mockList }),
      }),
    );
    const { knowledgeApi } = await import("@/lib/api/knowledge");
    const result = await knowledgeApi.listTechniques({
      category: "training",
      task_type: "det",
    });
    expect(result.items).toHaveLength(1);
    expect(result.items[0].technique_id).toBe("t-1");
  });

  it("test_listTechniques_passes_filter_params", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ok: true, data: { items: [], total: 0 } }),
      }),
    );
    const { knowledgeApi } = await import("@/lib/api/knowledge");
    await knowledgeApi.listTechniques({
      category: "training",
      layer: "augment",
      task_type: "det",
      maturity: "verified",
    });
    const url = (vi.mocked(fetch).mock.calls[0][0] as string);
    expect(url).toContain("category=training");
    expect(url).toContain("task_type=det");
  });

  // ──────────────────────────────────────────────────
  // getTechnique
  // ──────────────────────────────────────────────────
  it("test_getTechnique_returns_full_detail", async () => {
    const mockDetail = {
      technique_id: "t-1",
      name: "Mosaic数据增强",
      category: "training",
      layer: "augment",
      task_type: "det",
      conditions: [],
      actions: [],
      tradeoffs: [],
      evidences: [],
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ok: true, data: mockDetail }),
      }),
    );
    const { knowledgeApi } = await import("@/lib/api/knowledge");
    const result = await knowledgeApi.getTechnique("t-1");
    expect(result.technique_id).toBe("t-1");
    expect(result).toHaveProperty("conditions");
    expect(result).toHaveProperty("actions");
    expect(result).toHaveProperty("tradeoffs");
    expect(result).toHaveProperty("evidences");
  });
});
