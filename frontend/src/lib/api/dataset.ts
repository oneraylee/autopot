import { request } from "./request";

export interface DatasetVersion {
  dataset_id: string;
  version: number;
  manifest_uri: string;
  frozen: boolean;
  created_at: string;
}

export interface SceneLabel {
  frame_id: string;
  weather?: string;
  time_of_day?: string;
  road_type?: string;
  other_text?: string;
}

export interface SceneCoverage {
  dimensions: Record<string, Record<string, number>>;
}

export function importDatasetVersion(
  datasetId: string,
  body: { version: number; manifest_uri: string },
): Promise<DatasetVersion> {
  return request<DatasetVersion>(
    "POST",
    `/datasets/${encodeURIComponent(datasetId)}/versions/import`,
    { body },
  );
}

export function freezeDatasetVersion(
  datasetId: string,
  version: number,
): Promise<DatasetVersion> {
  return request<DatasetVersion>(
    "POST",
    `/datasets/${encodeURIComponent(datasetId)}/versions/${version}/freeze`,
  );
}

export function upsertSceneLabels(
  datasetVersionId: string,
  labels: SceneLabel[],
): Promise<{ count: number }> {
  return request<{ count: number }>(
    "PUT",
    `/datasets/versions/${encodeURIComponent(datasetVersionId)}/scene-labels`,
    { body: { labels } },
  );
}

export function getSceneCoverage(
  datasetVersionId: string,
  dimensions: string[],
): Promise<SceneCoverage> {
  return request<SceneCoverage>(
    "GET",
    `/datasets/versions/${encodeURIComponent(datasetVersionId)}/scene-coverage`,
    { params: { dimensions: dimensions.join(",") } },
  );
}
