import { describe, it, expect, vi, beforeEach } from "vitest";
import { getEvalReport, getEvidencePack, getAnalysisReport, getNextExperiments } from "@/lib/api/analysis";
import * as req from "@/lib/api/request";

vi.mock("@/lib/api/request");

const mockRequest = vi.mocked(req.request);

describe("analysis API client", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("test_get_eval_report_returns_valid_structure", async () => {
    const payload = {
      job_id: "j1",
      run_id: "r1",
      artifact_type: "eval",
      locator: "/path",
      locator_type: "fs",
      payload: {
        overall: { business_kpi: 0.9, kpi_components: { "漏检率": 0.03 } },
        by_class: [],
        by_scene: [],
      },
    };
    mockRequest.mockResolvedValue(payload);
    const result = await getEvalReport("j1", "r1");
    expect(mockRequest).toHaveBeenCalledWith("GET", "/jobs/j1/artifacts/eval-report", { params: { run_id: "r1" } });
    expect(result.payload.overall.business_kpi).toBe(0.9);
  });

  it("test_get_evidence_pack_returns_summary_and_index", async () => {
    const payload = {
      job_id: "j1",
      run_id: "r1",
      artifact_type: "evidence",
      locator: "/path",
      locator_type: "fs",
      payload: { summary: "ok", artifact_index: ["/a", "/b"], kpi_config: {} },
    };
    mockRequest.mockResolvedValue(payload);
    const result = await getEvidencePack("j1", "r1");
    expect(mockRequest).toHaveBeenCalledWith("GET", "/jobs/j1/artifacts/evidence-pack", { params: { run_id: "r1" } });
    expect(result.payload.artifact_index).toHaveLength(2);
  });

  it("test_run_id_required_for_all_artifact_apis", async () => {
    mockRequest.mockResolvedValue({});
    await getEvalReport("j1", "r1");
    await getEvidencePack("j1", "r1");
    await getAnalysisReport("j1", "r1");
    await getNextExperiments("j1", "r1");
    expect(mockRequest).toHaveBeenCalledTimes(4);
    for (const call of mockRequest.mock.calls) {
      expect(call[2]).toEqual(expect.objectContaining({ params: { run_id: "r1" } }));
    }
  });

  it("test_get_analysis_report_returns_payload", async () => {
    const payload = {
      job_id: "j1",
      run_id: "r1",
      artifact_type: "llm",
      locator: "/p",
      locator_type: "fs",
      payload: { analysis_report: "# Report\nSome analysis" },
    };
    mockRequest.mockResolvedValue(payload);
    const result = await getAnalysisReport("j1", "r1");
    expect(mockRequest).toHaveBeenCalledWith("GET", "/jobs/j1/artifacts/analysis-report", { params: { run_id: "r1" } });
    expect(result.payload.analysis_report).toContain("Report");
  });

  it("test_get_next_experiments_returns_candidates", async () => {
    const payload = {
      job_id: "j1",
      run_id: "r1",
      artifact_type: "llm",
      locator: "/p",
      locator_type: "fs",
      payload: {
        baseline_job_id: "j1",
        candidates: [
          { name: "A_test", changes: {}, expected: { kpi_delta: {} }, evidence_refs: [] },
        ],
      },
    };
    mockRequest.mockResolvedValue(payload);
    const result = await getNextExperiments("j1", "r1");
    expect(result.payload.candidates).toHaveLength(1);
    expect(result.payload.candidates[0].name).toBe("A_test");
  });
});
