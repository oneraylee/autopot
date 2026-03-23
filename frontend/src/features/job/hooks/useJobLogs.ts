"use client";

import { useQuery } from "@tanstack/react-query";
import { getJobLogs } from "@/lib/api/job";

export function useJobLogs(jobId: string, page: number, pageSize: number) {
  return useQuery({
    queryKey: ["job-logs", jobId, page, pageSize],
    queryFn: () => getJobLogs(jobId, page, pageSize),
    enabled: !!jobId,
  });
}
