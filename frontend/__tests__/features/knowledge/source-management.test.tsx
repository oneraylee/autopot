import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import fs from "fs";
import path from "path";
import { SourceList } from "@/features/knowledge/components/SourceList";
import { CreateSourceForm } from "@/features/knowledge/components/CreateSourceForm";
import { DocumentImportForm } from "@/features/knowledge/components/DocumentImportForm";
import { DocumentList } from "@/features/knowledge/components/DocumentList";
import { ChunkViewer } from "@/features/knowledge/components/ChunkViewer";
import { QueryState } from "@/components/QueryState";
import type { KnowledgeSource } from "@/features/knowledge/types";

const root = path.resolve(__dirname, "../../..");

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

// ──────────────────────────────────────────────────
// 文件存在性
// ──────────────────────────────────────────────────
describe("Phase6-Step2: 文件存在性 (SourceManagementGate)", () => {
  it("test_knowledge_landing_page_exists", () => {
    expect(
      fs.existsSync(
        path.join(root, "src/app/(dashboard)/knowledge/page.tsx"),
      ),
    ).toBe(true);
  });

  it("test_sources_page_exists", () => {
    expect(
      fs.existsSync(
        path.join(root, "src/app/(dashboard)/knowledge/sources/page.tsx"),
      ),
    ).toBe(true);
  });

  it("test_documents_page_exists", () => {
    expect(
      fs.existsSync(
        path.join(root, "src/app/(dashboard)/knowledge/documents/page.tsx"),
      ),
    ).toBe(true);
  });
});

// ──────────────────────────────────────────────────
// 侧栏 Knowledge 入口
// ──────────────────────────────────────────────────
describe("Phase6-Step2: 侧栏知识库入口", () => {
  it("test_sidebar_knowledge_entry_visible", async () => {
    const { Sidebar } = await import("@/components/Sidebar");
    render(<Sidebar />);
    expect(screen.getByTestId("nav-knowledge")).toBeInTheDocument();
  });
});

// ──────────────────────────────────────────────────
// SourceList 组件
// ──────────────────────────────────────────────────
describe("Phase6-Step2: SourceList", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("test_source_list_renders_columns", () => {
    const sources: KnowledgeSource[] = [
      {
        source_id: "s-1",
        source_type: "local" as const,
        name: "YOLO 资料",
        uri: "/docs/yolo.md",
        trust_level: 4,
        status: "active",
      },
    ];
    render(<SourceList sources={sources} />, { wrapper });
    expect(screen.getByText("YOLO 资料")).toBeInTheDocument();
    expect(screen.getByText("local")).toBeInTheDocument();
    expect(screen.getByText("active")).toBeInTheDocument();
  });

  it("test_empty_state_renders", () => {
    render(<SourceList sources={[]} />, { wrapper });
    expect(screen.getByText(/暂无/)).toBeInTheDocument();
  });

  it("test_loading_state_renders", () => {
    render(
      <QueryState isLoading={true} error={null}>
        <div>content</div>
      </QueryState>,
    );
    expect(screen.getByText(/加载中/)).toBeInTheDocument();
  });

  it("test_error_state_renders", () => {
    render(
      <QueryState isLoading={false} error={new Error("请求失败")}>
        <div>content</div>
      </QueryState>,
    );
    expect(screen.getByText(/请求失败/)).toBeInTheDocument();
  });
});

// ──────────────────────────────────────────────────
// CreateSourceForm 组件
// ──────────────────────────────────────────────────
describe("Phase6-Step2: CreateSourceForm", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("test_create_source_form_validation", async () => {
    const user = userEvent.setup();
    render(<CreateSourceForm onSuccess={() => {}} />, { wrapper });
    await user.click(screen.getByRole("button", { name: /注册|添加|创建/ }));
    await waitFor(() => {
      // Multiple validation errors are expected (one per empty field)
      const errors = screen.queryAllByText(/必填|required/i);
      expect(errors.length).toBeGreaterThan(0);
    });
  });

  it("test_create_source_success", async () => {
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
              name: "Test",
              uri: "/test",
              trust_level: 3,
              status: "active",
            },
          }),
      }),
    );
    const onSuccess = vi.fn();
    const user = userEvent.setup();
    render(<CreateSourceForm onSuccess={onSuccess} />, { wrapper });
    await user.type(screen.getByLabelText(/来源名称|名称/), "Test Source");
    await user.selectOptions(screen.getByLabelText(/来源类型|类型/), "local");
    await user.type(screen.getByLabelText(/URI|路径/), "/path/to/doc");
    await user.click(screen.getByRole("button", { name: /注册|添加|创建/ }));
    await waitFor(() => {
      expect(vi.mocked(fetch)).toHaveBeenCalled();
    });
  });

  it("test_create_source_duplicate_error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            ok: false,
            error: {
              code: "CONFLICT",
              message: "来源已存在：相同 source_type 与 uri",
              type: "conflict",
              details: null,
            },
          }),
      }),
    );
    const user = userEvent.setup();
    render(<CreateSourceForm onSuccess={() => {}} />, { wrapper });
    await user.type(screen.getByLabelText(/来源名称|名称/), "重复来源");
    await user.selectOptions(screen.getByLabelText(/来源类型|类型/), "web");
    await user.type(screen.getByLabelText(/URI|路径/), "https://example.com/doc");
    await user.click(screen.getByRole("button", { name: /注册|添加|创建/ }));
    await waitFor(() => {
      expect(screen.getByText(/来源已存在|相同 source_type 与 uri/)).toBeInTheDocument();
    });
  });
});

// ──────────────────────────────────────────────────
// DocumentImportForm 组件
// ──────────────────────────────────────────────────
describe("Phase6-Step2: DocumentImportForm", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("test_document_import_form_fields", () => {
    render(<DocumentImportForm sourceId="s-1" />, { wrapper });
    expect(screen.getByLabelText(/文档标题|标题/)).toBeInTheDocument();
    expect(screen.getByLabelText(/文档类型|类型/)).toBeInTheDocument();
    expect(screen.getByLabelText(/本地文件|文件上传/i)).toBeInTheDocument();
  });

  it("test_document_status_polling", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            ok: true,
            data: {
              document_id: "doc-1",
              parse_status: "pending",
              title: "Doc",
              doc_type: "markdown",
              source_id: "s-1",
            },
          }),
      }),
    );
    render(<DocumentList sourceId="s-1" />, { wrapper });
    await waitFor(() => {
      expect(vi.mocked(fetch)).toHaveBeenCalled();
    });
  });
});

// ──────────────────────────────────────────────────
// ChunkViewer 组件
// ──────────────────────────────────────────────────
describe("Phase6-Step2: ChunkViewer", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("test_chunk_viewer_fields", () => {
    const chunks = [
      {
        chunk_id: "c-1",
        section_path: "§ 1.1 概述",
        token_count: 128,
        keywords: ["YOLO", "mosaic"],
      },
    ];
    render(<ChunkViewer chunks={chunks} />, { wrapper });
    expect(screen.getByText("§ 1.1 概述")).toBeInTheDocument();
    expect(screen.getByTestId("token-count")).toHaveTextContent("128");
    expect(screen.getByText("YOLO")).toBeInTheDocument();
  });
});
