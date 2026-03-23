import { request } from "./request";

/* ---------- common artifact envelope ---------- */
export interface ArtifactEnvelope<T = unknown> {
  job_id: string;
  run_id: string;
  artifact_type: string;
  locator: string;
  locator_type: string;
  payload: T;
}

/* ---------- EvalReport types ---------- */
export interface EvalReportPayload {
  overall: {
    business_kpi: number;
    kpi_components: Record<string, number>;
  };
  by_class: Array<Record<string, unknown>>;
  by_scene: Array<{
    scene: Record<string, string>;
    kpi: number;
    fn: number;
    fp: number;
  }>;
  error_slices?: unknown[];
  artifacts?: Record<string, unknown>;
}

/* ---------- EvidencePack types ---------- */
export interface EvidencePackPayload {
  summary: string;
  artifact_index: string[];
  kpi_config: Record<string, unknown>;
}

/* ---------- AnalysisReport types ---------- */
export interface AnalysisReportPayload {
  analysis_report: string;
}

/* ---------- NextExperiments types ---------- */
export interface Candidate {
  name: string;
  changes: Record<string, unknown>;
  expected: { kpi_delta: Record<string, number> };
  evidence_refs: string[];
}

export interface NextExperimentsPayload {
  baseline_job_id: string;
  candidates: Candidate[];
}

/* ---------- API methods ---------- */

export function getEvalReport(jobId: string, runId: string) {
  return request<ArtifactEnvelope<EvalReportPayload>>(
    "GET",
    `/jobs/${encodeURIComponent(jobId)}/artifacts/eval-report`,
    { params: { run_id: runId } },
  );
}

export function getEvidencePack(jobId: string, runId: string) {
  return request<ArtifactEnvelope<EvidencePackPayload>>(
    "GET",
    `/jobs/${encodeURIComponent(jobId)}/artifacts/evidence-pack`,
    { params: { run_id: runId } },
  );
}

export function getAnalysisReport(jobId: string, runId: string) {
  return request<ArtifactEnvelope<AnalysisReportPayload>>(
    "GET",
    `/jobs/${encodeURIComponent(jobId)}/artifacts/analysis-report`,
    { params: { run_id: runId } },
  );
}

export function getNextExperiments(jobId: string, runId: string) {
  return request<ArtifactEnvelope<NextExperimentsPayload>>(
    "GET",
    `/jobs/${encodeURIComponent(jobId)}/artifacts/next-experiments`,
    { params: { run_id: runId } },
  );
}
