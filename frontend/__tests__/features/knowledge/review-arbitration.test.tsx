import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import fs from "fs";
import path from "path";
import { SkillExtractReview } from "@/features/knowledge/components/SkillExtractReview";
import { ConflictArbitration } from "@/features/knowledge/components/ConflictArbitration";
import type { ConflictPair, SkillCandidate } from "@/features/knowledge/types";

const root = path.resolve(__dirname, "../../..");

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

const MOCK_CANDIDATES: SkillCandidate[] = [
  {
    candidate_id: "cand-1",
    name: "Mosaic 数据增强",
    category: "training",
    layer: "augment",
    condition: "小目标比例 >= 25%",
    action: "启用 mosaic=True",
    tradeoff: "轻微提升训练耗时",
  },
];

const MOCK_CONFLICT: ConflictPair = {
  conflict_id: "conf-1",
  technique_a: {
    technique_id: "t-1",
    name: "Mosaic 数据增强",
    summary: "使用马赛克增强",
  },
  technique_b: {
    technique_id: "t-2",
    name: "CopyPaste 增强",
    summary: "使用 CopyPaste 增强",
  },
  conflict_type: "incompatible_with",
  llm_suggestion: "建议保留 Mosaic，CopyPaste 可在更大数据集上使用",
};

// ──────────────────────────────────────────────────
// 文件存在性
// ──────────────────────────────────────────────────
describe("Phase6-Step4: 文件存在性 (ReviewArbitrationGate)", () => {
  it("test_review_page_exists", () => {
    expect(
      fs.existsSync(
        path.join(root, "src/app/(dashboard)/knowledge/review/page.tsx"),
      ),
    ).toBe(true);
  });
});

// ──────────────────────────────────────────────────
// SkillExtractReview 组件
// ──────────────────────────────────────────────────
describe("Phase6-Step4: SkillExtractReview", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("test_trigger_extraction_from_document", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({ ok: true, data: { candidates: MOCK_CANDIDATES } }),
      }),
    );
    const user = userEvent.setup();
    render(
      <SkillExtractReview documentId="doc-1" />,
      { wrapper },
    );
    await user.click(screen.getByRole("button", { name: /抽取|提取/ }));
    await waitFor(() => {
      expect(vi.mocked(fetch)).toHaveBeenCalledWith(
        expect.stringContaining("/knowledge/techniques/extract"),
        expect.any(Object),
      );
    });
  });

  it("test_candidate_list_renders", () => {
    render(
      <SkillExtractReview
        documentId="doc-1"
        candidates={MOCK_CANDIDATES}
      />,
      { wrapper },
    );
    expect(screen.getByText("Mosaic 数据增强")).toBeInTheDocument();
    // category/layer 展示格式为 "{category} / {layer}"，即 "training / augment"
    expect(screen.getByText("training / augment")).toBeInTheDocument();
    expect(screen.getByText("小目标比例 >= 25%")).toBeInTheDocument();
  });

  it("test_confirm_action_creates_skill", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            ok: true,
            data: {
              technique_id: "t-new",
              name: "Mosaic 数据增强",
              category: "training",
            },
          }),
      }),
    );
    const user = userEvent.setup();
    render(
      <SkillExtractReview
        documentId="doc-1"
        candidates={MOCK_CANDIDATES}
      />,
      { wrapper },
    );
    await user.click(screen.getByRole("button", { name: /确认/ }));
    await waitFor(() => {
      expect(vi.mocked(fetch)).toHaveBeenCalledWith(
        expect.stringContaining("/knowledge/techniques"),
        expect.any(Object),
      );
    });
  });

  it("test_modify_action_opens_edit_form", async () => {
    const user = userEvent.setup();
    render(
      <SkillExtractReview
        documentId="doc-1"
        candidates={MOCK_CANDIDATES}
      />,
      { wrapper },
    );
    await user.click(screen.getByRole("button", { name: /修改|编辑/ }));
    await waitFor(() => {
      expect(
        screen.getByLabelText(/技能编码|skill_code/i) ||
          screen.getByLabelText(/技能名称|名称/i),
      ).toBeInTheDocument();
    });
  });

  it("test_reject_action_removes_candidate", async () => {
    const user = userEvent.setup();
    render(
      <SkillExtractReview
        documentId="doc-1"
        candidates={MOCK_CANDIDATES}
      />,
      { wrapper },
    );
    expect(screen.getByText("Mosaic 数据增强")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /拒绝|忽略/ }));
    await waitFor(() => {
      expect(screen.queryByText("Mosaic 数据增强")).toBeNull();
    });
  });
});

// ──────────────────────────────────────────────────
// ConflictArbitration 组件
// ──────────────────────────────────────────────────
describe("Phase6-Step4: ConflictArbitration", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("test_conflict_pair_display", () => {
    render(
      <ConflictArbitration conflicts={[MOCK_CONFLICT]} />,
      { wrapper },
    );
    expect(screen.getByText("Mosaic 数据增强")).toBeInTheDocument();
    expect(screen.getByText("CopyPaste 增强")).toBeInTheDocument();
    expect(screen.getByText(/incompatible_with/)).toBeInTheDocument();
    expect(screen.getByText(/建议保留 Mosaic/)).toBeInTheDocument();
  });

  it("test_arbitration_options_available", () => {
    render(
      <ConflictArbitration conflicts={[MOCK_CONFLICT]} />,
      { wrapper },
    );
    // 四个仲裁选项
    expect(screen.getByText(/保A|保留A/)).toBeInTheDocument();
    expect(screen.getByText(/保B|保留B/)).toBeInTheDocument();
    expect(screen.getByText(/分流|条件分流/)).toBeInTheDocument();
    expect(screen.getByText(/标记|实验验证/)).toBeInTheDocument();
  });

  it("test_arbitration_writes_relation", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({ ok: true, data: { relation_id: "rel-1" } }),
      }),
    );
    const user = userEvent.setup();
    render(
      <ConflictArbitration conflicts={[MOCK_CONFLICT]} />,
      { wrapper },
    );
    await user.click(screen.getByText(/保A|保留A/));
    await user.click(screen.getByRole("button", { name: /确认仲裁|提交/ }));
    await waitFor(() => {
      expect(vi.mocked(fetch)).toHaveBeenCalledWith(
        expect.stringContaining("/knowledge/retrieval/resolve-conflicts"),
        expect.any(Object),
      );
    });
  });
});
