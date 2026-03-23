import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { ArtifactTabs } from "@/features/job/components/ArtifactTabs";
import { useJobArtifacts } from "@/features/job/hooks/useJobArtifacts";

// Mock the artifact components
vi.mock("@/features/job/components/EvalReport", () => ({
  EvalReport: ({ data }: { data: unknown }) => <div data-testid="eval-report">EvalReport</div>,
}));
vi.mock("@/features/job/components/EvidencePack", () => ({
  EvidencePack: ({ data }: { data: unknown }) => <div data-testid="evidence-pack">EvidencePack</div>,
}));
vi.mock("@/features/job/components/AnalysisReport", () => ({
  AnalysisReport: ({ content }: { content: string }) => <div data-testid="analysis-report">AnalysisReport</div>,
}));
vi.mock("@/features/job/components/NextExperiments", () => ({
  NextExperiments: (props: unknown) => <div data-testid="next-experiments">NextExperiments</div>,
}));

describe("ArtifactTabs", () => {
  const artifacts = {
    evalReport: {
      overall: { business_kpi: 0.9, kpi_components: {} },
      by_class: [],
      by_scene: [],
    },
    evidencePack: {
      summary: "ok",
      artifact_index: [],
      kpi_config: {},
    },
    analysisReport: "# Report",
    nextExperiments: {
      baseline_job_id: "j1",
      candidates: [],
    },
  };

  it("test_artifact_tabs_render_four_tabs", () => {
    render(<ArtifactTabs jobId="j1" artifacts={artifacts} />);
    expect(screen.getByText("评估报告")).toBeInTheDocument();
    expect(screen.getByText("证据包")).toBeInTheDocument();
    expect(screen.getByText("分析报告")).toBeInTheDocument();
    expect(screen.getByText("候选实验")).toBeInTheDocument();
  });

  it("test_tab_switch_loads_correct_artifact", () => {
    render(<ArtifactTabs jobId="j1" artifacts={artifacts} />);
    // Default tab shows eval report
    expect(screen.getByTestId("eval-report")).toBeInTheDocument();

    fireEvent.click(screen.getByText("证据包"));
    expect(screen.getByTestId("evidence-pack")).toBeInTheDocument();

    fireEvent.click(screen.getByText("分析报告"));
    expect(screen.getByTestId("analysis-report")).toBeInTheDocument();

    fireEvent.click(screen.getByText("候选实验"));
    expect(screen.getByTestId("next-experiments")).toBeInTheDocument();
  });

  it("test_tabs_disabled_when_no_artifacts", () => {
    render(<ArtifactTabs jobId="j1" artifacts={null} />);
    expect(screen.getByText(/暂无产物数据/)).toBeInTheDocument();
  });

  it("test_partial_artifacts_only_show_available", () => {
    const partial = {
      evalReport: artifacts.evalReport,
      evidencePack: null,
      analysisReport: null,
      nextExperiments: null,
    };
    render(<ArtifactTabs jobId="j1" artifacts={partial} />);
    // eval tab should work
    expect(screen.getByTestId("eval-report")).toBeInTheDocument();
    // switch to missing tab should show empty state
    fireEvent.click(screen.getByText("证据包"));
    expect(screen.getByText(/暂无数据/)).toBeInTheDocument();
  });
});

// ===== Integration Tests =====

function qcWrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("ArtifactTabs real data integration", () => {
  const fullArtifacts = {
    evalReport: {
      overall: { business_kpi: 0.92, kpi_components: { precision: 0.95 } },
      by_class: [{ class_name: "car", kpi: 0.93 }],
      by_scene: [{ scene: { weather: "rain" }, kpi: 0.88, fn: 5, fp: 3 }],
    },
    evidencePack: {
      summary: "Evidence pack summary",
      artifact_index: ["artifact/1.png"],
      kpi_config: { safety: { ttp: 0.5 } },
    },
    analysisReport: "# Analysis Report",
    nextExperiments: {
      baseline_job_id: "j-1",
      candidates: [
        {
          name: "Candidate A",
          changes: { lr: 0.001 },
          expected: { kpi_delta: { business_kpi: -0.02 } },
          evidence_refs: ["ref1"],
        },
      ],
    },
  };

  it("test_artifact_tabs_load_real_eval_evidence_analysis_and_candidates", () => {
    render(<ArtifactTabs jobId="j-1" artifacts={fullArtifacts} />);

    // Eval tab: component rendered, not empty state
    expect(screen.getByTestId("eval-report")).toBeInTheDocument();
    expect(screen.queryByText("暂无数据")).not.toBeInTheDocument();

    // Evidence tab
    fireEvent.click(screen.getByText("证据包"));
    expect(screen.getByTestId("evidence-pack")).toBeInTheDocument();

    // Analysis tab
    fireEvent.click(screen.getByText("分析报告"));
    expect(screen.getByTestId("analysis-report")).toBeInTheDocument();

    // Experiments tab
    fireEvent.click(screen.getByText("候选实验"));
    expect(screen.getByTestId("next-experiments")).toBeInTheDocument();
  });

  it("test_artifact_tabs_show_empty_state_when_payload_missing", () => {
    const emptyPayload = {
      evalReport: null,
      evidencePack: null,
      analysisReport: null,
      nextExperiments: null,
    };
    render(<ArtifactTabs jobId="j-1" artifacts={emptyPayload} />);

    // Tabs should still be visible
    expect(screen.getByText("评估报告")).toBeInTheDocument();
    // Default tab (eval) shows empty state
    expect(screen.getByText("暂无数据")).toBeInTheDocument();
  });
});

describe("useJobArtifacts hook", () => {
  const originalFetch = globalThis.fetch;

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("test_job_detail_never_passes_null_artifacts_after_query_success", async () => {
    const base = { job_id: "j-1", run_id: "j-1", locator: "/tmp", locator_type: "local" };
    const mockFetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes("eval-report")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              ok: true,
              data: {
                ...base,
                artifact_type: "eval_report",
                payload: { overall: { business_kpi: 0.9, kpi_components: {} }, by_class: [], by_scene: [] },
              },
            }),
        });
      }
      if (url.includes("evidence-pack")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              ok: true,
              data: {
                ...base,
                artifact_type: "evidence_pack",
                payload: { summary: "ok", artifact_index: [], kpi_config: {} },
              },
            }),
        });
      }
      if (url.includes("analysis-report")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              ok: true,
              data: {
                ...base,
                artifact_type: "analysis_report",
                payload: { analysis_report: "# Report" },
              },
            }),
        });
      }
      if (url.includes("next-experiments")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              ok: true,
              data: {
                ...base,
                artifact_type: "next_experiments",
                payload: { baseline_job_id: "j-1", candidates: [] },
              },
            }),
        });
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    });
    globalThis.fetch = mockFetch;

    const { result } = renderHook(() => useJobArtifacts("j-1"), { wrapper: qcWrapper });

    await waitFor(() => {
      expect(result.current.data).not.toBeNull();
    });
    expect(result.current.data!.evalReport).not.toBeNull();
    expect(result.current.data!.evidencePack).not.toBeNull();
    expect(result.current.data!.analysisReport).not.toBeNull();
    expect(result.current.data!.nextExperiments).not.toBeNull();
  });
});
