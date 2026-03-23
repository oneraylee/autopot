"use client";

import { useQuery } from "@tanstack/react-query";
import { request } from "@/lib/api/request";
import type { Job } from "@/lib/api/job";

export function useJobList() {
  return useQuery<Job[]>({
    queryKey: ["jobs"],
    queryFn: () => request<Job[]>("GET", "/jobs"),
  });
}
