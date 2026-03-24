"use client";

import { useState } from "react";
import { QueryState } from "@/components/QueryState";
import { ProviderList } from "@/features/settings/components/ProviderList";
import { UsageReport } from "@/features/settings/components/UsageReport";
import { CallLogList } from "@/features/settings/components/CallLogList";
import { useCallLogs, useProviders, useUsageReport } from "@/features/settings/hooks/useGateway";
import type { CallLogParams, UsageReportParams } from "@/lib/api/llm-gateway";

export default function LlmGatewayPage() {
  const [usageParams, setUsageParams] = useState<UsageReportParams>({ group_by: "provider" });
  const [logParams, setLogParams] = useState<CallLogParams>({ page: 1, page_size: 20 });

  const providersQuery = useProviders();
  const usageQuery = useUsageReport(usageParams);
  const logsQuery = useCallLogs(logParams);

  return (
    <div className="space-y-8">
      <h1 className="text-xl font-semibold">LLM Gateway</h1>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Provider 列表</h2>
        <QueryState
          isLoading={providersQuery.isLoading}
          error={providersQuery.error as Error | null}
          isEmpty={(providersQuery.data ?? []).length === 0}
          emptyMessage="暂无 Provider 数据"
        >
          <ProviderList providers={providersQuery.data ?? []} />
        </QueryState>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">用量报表</h2>
        <QueryState
          isLoading={usageQuery.isLoading}
          error={usageQuery.error as Error | null}
        >
          <UsageReport
            data={usageQuery.data ?? { items: [], total_tokens: 0, total_cost: 0 }}
            onParamsChange={(next) => setUsageParams((current) => ({ ...current, ...next }))}
            isLoading={usageQuery.isLoading}
          />
        </QueryState>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">调用日志</h2>
        <QueryState
          isLoading={logsQuery.isLoading}
          error={logsQuery.error as Error | null}
        >
          <CallLogList
            data={logsQuery.data ?? { items: [], page: 1, page_size: 20, total: 0 }}
            onPageChange={(page) => setLogParams((current) => ({ ...current, page }))}
            onFilterChange={(next) => setLogParams((current) => ({ ...current, page: 1, ...next }))}
            isLoading={logsQuery.isLoading}
          />
        </QueryState>
      </section>
    </div>
  );
}