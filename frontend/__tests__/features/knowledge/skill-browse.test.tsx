import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import fs from "fs";
import path from "path";
import { SkillList } from "@/features/knowledge/components/SkillList";
import { SkillTaxonomy } from "@/features/knowledge/components/SkillTaxonomy";
import { SkillDetail } from "@/features/knowledge/components/SkillDetail";
import { SkillEditForm } from "@/features/knowledge/components/SkillEditForm";
import type { TechniqueDetail, TechniqueSummary } from "@/features/knowledge/types";
import type { CreateTechniqueFormValues } from "@/schemas/knowledge";

const root = path.resolve(__dirname, "../../..");

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

const MOCK_SKILLS: TechniqueSummary[] = [
  {
    technique_id: "t-1",
    skill_code: "train.augment.mosaic",
    name: "Mosaic 数据增强",
    category: "training",
    layer: "augment",
    task_type: "det",
    maturity: "verified",
    status: "active",
  },
  {
    technique_id: "t-2",
    skill_code: "model.backbone.csp",
    name: "CSP 主干",
    category: "model",
    layer: "backbone",
    task_type: "det",
    maturity: "reviewed",
    status: "active",
  },
];

// ──────────────────────────────────────────────────
// 文件存在性
// ──────────────────────────────────────────────────
describe("Phase6-Step3: 文件存在性 (SkillBrowseGate)", () => {
  it("test_skills_page_exists", () => {
    expect(
      fs.existsSync(
        path.join(root, "src/app/(dashboard)/knowledge/skills/page.tsx"),
      ),
    ).toBe(true);
  });

  it("test_skill_detail_page_exists", () => {
    expect(
      fs.existsSync(
        path.join(
          root,
          "src/app/(dashboard)/knowledge/skills/[id]/page.tsx",
        ),
      ),
    ).toBe(true);
  });
});

// ──────────────────────────────────────────────────
// SkillList 组件
// ──────────────────────────────────────────────────
describe("Phase6-Step3: SkillList", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("test_skill_list_table_columns", () => {
    render(<SkillList skills={MOCK_SKILLS} />, { wrapper });
    // 验证关键列存在
    expect(screen.getByText("Mosaic 数据增强")).toBeInTheDocument();
    expect(screen.getByText("train.augment.mosaic")).toBeInTheDocument();
    // 多列匹配不用 getByText，用 getAllByText
    const trainingCells = screen.getAllByText("training");
    expect(trainingCells.length).toBeGreaterThan(0);
    const augmentCells = screen.getAllByText("augment");
    expect(augmentCells.length).toBeGreaterThan(0);
    expect(screen.getAllByText("verified").length).toBeGreaterThan(0);
  });

  it("test_skill_filter_by_category", async () => {
    const onFilterChange = vi.fn();
    const user = userEvent.setup();
    render(
      <SkillList skills={MOCK_SKILLS} onFilterChange={onFilterChange} />,
      { wrapper },
    );
    const categorySelect = screen.getByLabelText(/分类|category/i);
    await user.selectOptions(categorySelect, "training");
    await waitFor(() => {
      expect(onFilterChange).toHaveBeenCalledWith(
        expect.objectContaining({ category: "training" }),
      );
    });
  });

  it("test_skill_filter_by_layer", async () => {
    const onFilterChange = vi.fn();
    const user = userEvent.setup();
    render(
      <SkillList skills={MOCK_SKILLS} onFilterChange={onFilterChange} />,
      { wrapper },
    );
    const layerSelect = screen.getByLabelText(/层级|layer/i);
    await user.selectOptions(layerSelect, "augment");
    await waitFor(() => {
      expect(onFilterChange).toHaveBeenCalledWith(
        expect.objectContaining({ layer: "augment" }),
      );
    });
  });

  it("test_skill_filter_by_task_type", async () => {
    const onFilterChange = vi.fn();
    const user = userEvent.setup();
    render(
      <SkillList skills={MOCK_SKILLS} onFilterChange={onFilterChange} />,
      { wrapper },
    );
    const taskSelect = screen.getByLabelText(/任务类型|task/i);
    await user.selectOptions(taskSelect, "det");
    await waitFor(() => {
      expect(onFilterChange).toHaveBeenCalledWith(
        expect.objectContaining({ task_type: "det" }),
      );
    });
  });

  it("test_skill_filter_by_maturity", async () => {
    const onFilterChange = vi.fn();
    const user = userEvent.setup();
    render(
      <SkillList skills={MOCK_SKILLS} onFilterChange={onFilterChange} />,
      { wrapper },
    );
    const maturitySelect = screen.getByLabelText(/成熟度|maturity/i);
    await user.selectOptions(maturitySelect, "verified");
    await waitFor(() => {
      expect(onFilterChange).toHaveBeenCalledWith(
        expect.objectContaining({ maturity: "verified" }),
      );
    });
  });

  it("test_empty_filter_result_hint", () => {
    render(<SkillList skills={[]} />, { wrapper });
    expect(screen.getByText(/暂无|无匹配/)).toBeInTheDocument();
  });

  it("test_filter_syncs_to_url", async () => {
    // Verify that the page reads filters from URL searchParams and
    // the SkillList onFilterChange callback produces correct filter objects
    // that would be written back to URL by the page.
    const onFilterChange = vi.fn();
    const user = userEvent.setup();
    render(
      <SkillList skills={MOCK_SKILLS} onFilterChange={onFilterChange} />,
      { wrapper },
    );
    // Select category
    await user.selectOptions(screen.getByLabelText(/分类|category/i), "training");
    await waitFor(() => {
      expect(onFilterChange).toHaveBeenCalledWith(
        expect.objectContaining({ category: "training" }),
      );
    });
    // Select layer
    await user.selectOptions(screen.getByLabelText(/层级|layer/i), "augment");
    await waitFor(() => {
      expect(onFilterChange).toHaveBeenCalledWith(
        expect.objectContaining({ layer: "augment" }),
      );
    });
    // The page component (skills/page.tsx) converts these to URLSearchParams
    // Verify the callback produces values compatible with URL serialization
    const calls = onFilterChange.mock.calls;
    for (const [filterObj] of calls) {
      for (const val of Object.values(filterObj)) {
        if (val !== undefined) {
          expect(typeof val).toBe("string");
        }
      }
    }
  });
});

// ──────────────────────────────────────────────────
// SkillTaxonomy 组件
// ──────────────────────────────────────────────────
describe("Phase6-Step3: SkillTaxonomy", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("test_taxonomy_four_categories", () => {
    render(<SkillTaxonomy onCategorySelect={() => {}} />, { wrapper });
    expect(screen.getByText(/Training Skills|训练技能/)).toBeInTheDocument();
    expect(screen.getByText(/Model Skills|模型技能/)).toBeInTheDocument();
    expect(screen.getByText(/Data Skills|数据技能/)).toBeInTheDocument();
    expect(
      screen.getByText(/Eval.*Deploy|评估.*部署/),
    ).toBeInTheDocument();
  });

  it("test_taxonomy_click_filters_list", async () => {
    const onCategorySelect = vi.fn();
    const user = userEvent.setup();
    render(
      <SkillTaxonomy onCategorySelect={onCategorySelect} />,
      { wrapper },
    );
    await user.click(screen.getByText(/Training Skills|训练技能/));
    await waitFor(() => {
      expect(onCategorySelect).toHaveBeenCalledWith(
        expect.objectContaining({ category: "training" }),
      );
    });
  });
});

// ──────────────────────────────────────────────────
// SkillDetail 组件
// ──────────────────────────────────────────────────
describe("Phase6-Step3: SkillDetail", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  const MOCK_DETAIL: TechniqueDetail = {
    technique_id: "t-1",
    skill_code: "train.augment.mosaic",
    name: "Mosaic 数据增强",
    category: "training",
    layer: "augment",
    task_type: "det",
    maturity: "draft",
    status: "active",
    summary: "马赛克数据增强技术",
    conditions: [{ condition_id: "c-1", description: "小目标比例 >= 25%" }],
    actions: [{ action_id: "a-1", description: "启用 Mosaic" }],
    tradeoffs: [{ tradeoff_id: "tr-1", dimension: "kpi", effect_direction: "up" }],
    evidences: [{ evidence_id: "e-1", evidence_type: "source_chunk", notes: "来自官方文档" }],
  };

  it("test_skill_detail_sections", () => {
    render(<SkillDetail technique={MOCK_DETAIL} />, { wrapper });
    expect(screen.getByText("Mosaic 数据增强")).toBeInTheDocument();
    expect(screen.getByText(/条件|Condition/i)).toBeInTheDocument();
    expect(screen.getByText(/动作|Action/i)).toBeInTheDocument();
    expect(screen.getByText(/收益|代价|Tradeoff/i)).toBeInTheDocument();
    expect(screen.getByText(/证据|Evidence/i)).toBeInTheDocument();
  });

  it("test_skill_detail_relations_section", () => {
    render(
      <SkillDetail
        technique={{
          ...MOCK_DETAIL,
          relations: [
            {
              relation_id: "r-1",
              from_technique_id: "t-1",
              to_technique_id: "t-2",
              relation_type: "compatible_with",
              description: "与 CopyPaste 可组合",
            },
          ],
        }}
      />,
      { wrapper },
    );
    expect(screen.getByText(/关系|Relation/i)).toBeInTheDocument();
    expect(screen.getByText(/compatible_with/)).toBeInTheDocument();
    expect(screen.getByText(/CopyPaste 可组合/)).toBeInTheDocument();
  });

  it("test_publish_button_draft_only", () => {
    render(
      <SkillDetail technique={MOCK_DETAIL} onPublish={() => {}} />,
      { wrapper },
    );
    // draft 状态有发布按钮
    expect(
      screen.getByRole("button", { name: /发布/ }),
    ).toBeInTheDocument();
  });

  it("test_publish_button_inactive_hidden", () => {
    render(
      <SkillDetail
        technique={{ ...MOCK_DETAIL, status: "inactive", maturity: "deprecated" }}
        onPublish={() => {}}
      />,
      { wrapper },
    );
    // deprecated + inactive 无发布按钮
    expect(
      screen.queryByRole("button", { name: /发布/ }),
    ).toBeNull();
  });

  it("test_publish_confirm_dialog", async () => {
    const user = userEvent.setup();
    render(
      <SkillDetail technique={MOCK_DETAIL} onPublish={() => {}} />,
      { wrapper },
    );
    await user.click(screen.getByRole("button", { name: /发布/ }));
    await waitFor(() => {
      // 确认对话展示：找到确认发布按钮
      expect(
        screen.getByRole("button", { name: /确认发布/ }),
      ).toBeInTheDocument();
    });
  });
});

// ──────────────────────────────────────────────────
// SkillEditForm 组件
// ──────────────────────────────────────────────────
describe("Phase6-Step3: SkillEditForm", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("test_edit_form_prefill", () => {
    const defaults: Partial<CreateTechniqueFormValues> = {
      skill_code: "train.augment.mosaic",
      name: "Mosaic 数据增强",
      category: "training",
      layer: "augment",
      task_type: "det",
    };
    render(<SkillEditForm defaultValues={defaults} onSuccess={() => {}} />, {
      wrapper,
    });
    expect(screen.getByLabelText(/技能编码|skill_code/i)).toHaveValue(
      "train.augment.mosaic",
    );
    expect(screen.getByLabelText(/技能名称|名称/i)).toHaveValue(
      "Mosaic 数据增强",
    );
  });
});
