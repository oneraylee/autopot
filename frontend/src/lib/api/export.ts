import { request } from "./request";

export interface ExportTask {
  export_id: string;
  job_id: string;
  run_id: string;
  backend: string;
  status: string;
  created_at: string;
}

export interface DeployBenchmark {
  latency_ms: number;
  throughput_fps: number;
  memory_mb: number;
}

export function createExport(body: {
  job_id: string;
  run_id: string;
  backend: string;
}): Promise<ExportTask> {
  return request<ExportTask>("POST", "/exports", { body });
}

export function getExportStatus(exportId: string): Promise<ExportTask> {
  return request<ExportTask>(
    "GET",
    `/exports/${encodeURIComponent(exportId)}`,
  );
}

export function getDeployBenchmark(exportId: string): Promise<DeployBenchmark> {
  return request<DeployBenchmark>(
    "GET",
    `/exports/${encodeURIComponent(exportId)}/deploy-benchmark`,
  );
}
