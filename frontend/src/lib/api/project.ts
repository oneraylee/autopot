import { request } from "./request";

export interface DeployConstraint {
  metric: string;
  operator: string;
  value: number;
}

export interface KpiConfig {
  primary_kpi: string;
  threshold: number;
  weights: { eval: number; deploy: number };
  deploy_constraints: DeployConstraint[];
}

export function getKpiConfig(projectId: string): Promise<KpiConfig> {
  return request<KpiConfig>("GET", `/projects/${encodeURIComponent(projectId)}/kpi-config`);
}

export function updateKpiConfig(
  projectId: string,
  config: KpiConfig,
): Promise<KpiConfig> {
  return request<KpiConfig>(
    "PUT",
    `/projects/${encodeURIComponent(projectId)}/kpi-config`,
    { body: config },
  );
}
