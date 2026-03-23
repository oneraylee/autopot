"use client";

import { useQuery } from "@tanstack/react-query";
import { request } from "@/lib/api/request";

export interface DatasetSummary {
  dataset_id: string;
  name: string;
  latest_version: number;
  created_at: string;
}

export function useDatasetList() {
  return useQuery<DatasetSummary[]>({
    queryKey: ["datasets"],
    queryFn: () => request<DatasetSummary[]>("GET", "/datasets"),
  });
}
