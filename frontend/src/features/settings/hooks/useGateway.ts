"use client";

import { useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getCallLogs,
  getUsageReport,
  listProviders,
  type CallLogParams,
  type UsageReportParams,
} from "@/lib/api/llm-gateway";

export function useProviders() {
  return useQuery({
    queryKey: ["llm-gateway", "providers"],
    queryFn: listProviders,
  });
}

export function useUsageReport(params: UsageReportParams) {
  return useQuery({
    queryKey: ["llm-gateway", "usage", params],
    queryFn: () => getUsageReport(params),
  });
}

export function useCallLogs(params: CallLogParams) {
  const queryClient = useQueryClient();

  useEffect(() => {
    return () => {
      queryClient.removeQueries({ queryKey: ["llm-gateway", "call-logs"] });
    };
  }, [queryClient]);

  return useQuery({
    queryKey: ["llm-gateway", "call-logs", params],
    queryFn: () => getCallLogs(params),
  });
}