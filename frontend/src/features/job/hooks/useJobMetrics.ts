"use client";

import { useQuery } from "@tanstack/react-query";
import { getJobMetrics } from "@/lib/api/job";

export function useJobMetrics(jobId: string, startTs: number, endTs: number) {
  return useQuery({
    queryKey: ["job-metrics", jobId, startTs, endTs],
    queryFn: () => getJobMetrics(jobId, startTs, endTs),
    enabled: !!jobId,
  });
}
