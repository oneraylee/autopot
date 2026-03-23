import { request } from "./request";

export type JobStatus =
  | "created"
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "canceled"
  | "evaluating"
  | "eval_succeeded"
  | "eval_failed"
  | "evidence_ready"
  | "llm_analyzing"
  | "llm_done"
  | "llm_failed";

export type TaskType = "training" | "evaluation" | "analysis" | "export";

export interface Job {
  job_id: string;
  task_type: TaskType;
  status: JobStatus;
  dataset_version_id: string;
  created_at: string;
  updated_at: string;
}

export interface LogEntry {
  line: number;
  message: string;
}

export interface LogPage {
  items: LogEntry[];
  page: number;
  page_size: number;
  total: number;
}

export interface MetricPoint {
  ts: number;
  values: Record<string, number>;
}

export interface MetricsResult {
  items: MetricPoint[];
  window: { start_ts: number; end_ts: number };
}

export function getJob(jobId: string): Promise<Job> {
  return request<Job>("GET", `/jobs/${encodeURIComponent(jobId)}`);
}

export function getJobLogs(
  jobId: string,
  page: number,
  pageSize: number,
): Promise<LogPage> {
  return request<LogPage>("GET", `/jobs/${encodeURIComponent(jobId)}/logs`, {
    params: { page: String(page), page_size: String(pageSize) },
  });
}

export function getJobMetrics(
  jobId: string,
  startTs: number,
  endTs: number,
): Promise<MetricsResult> {
  return request<MetricsResult>(
    "GET",
    `/jobs/${encodeURIComponent(jobId)}/metrics`,
    { params: { start_ts: String(startTs), end_ts: String(endTs) } },
  );
}

export interface CreateJobPayload {
  task_type: string;
  dataset_version_id: string;
  config: Record<string, unknown>;
  resources: { gpu_count: number };
}

export function createJob(payload: CreateJobPayload): Promise<Job> {
  return request<Job>("POST", "/jobs", { body: payload });
}

export function startJob(
  jobId: string,
  body: { gpu_id: string },
): Promise<Job> {
  return request<Job>("POST", `/jobs/${encodeURIComponent(jobId)}/start`, {
    body,
  });
}
