"use client";

import { useQuery } from "@tanstack/react-query";
import { getJob } from "@/lib/api/job";

export function useJob(jobId: string) {
  return useQuery({
    queryKey: ["job", jobId],
    queryFn: () => getJob(jobId),
    enabled: !!jobId,
  });
}
