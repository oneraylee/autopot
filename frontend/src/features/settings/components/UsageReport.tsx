"use client";

import { BarChart, Bar, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { UsageReportParams, UsageReportResponse } from "@/lib/api/llm-gateway";

interface UsageReportProps {
  data: UsageReportResponse;
  onParamsChange: (params: Partial<UsageReportParams>) => void;
  isLoading: boolean;
}

export function UsageReport({ data, onParamsChange, isLoading }: UsageReportProps) {
  const hasData = data.items.length > 0;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <input
          data-testid="usage-start-date"
          type="date"
          className="rounded border px-3 py-2 text-sm"
          onChange={(event) => onParamsChange({ start_date: event.target.value })}
        />
        <input
          data-testid="usage-end-date"
          type="date"
          className="rounded border px-3 py-2 text-sm"
          onChange={(event) => onParamsChange({ end_date: event.target.value })}
        />
        <div className="flex gap-2">
          <button data-testid="group-by-provider" className="rounded border px-3 py-2 text-sm" onClick={() => onParamsChange({ group_by: "provider" })}>provider</button>
          <button data-testid="group-by-call_type" className="rounded border px-3 py-2 text-sm" onClick={() => onParamsChange({ group_by: "call_type" })}>call_type</button>
          <button data-testid="group-by-model" className="rounded border px-3 py-2 text-sm" onClick={() => onParamsChange({ group_by: "model" })}>model</button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
        <div className="rounded border p-3">总 Token: {data.total_tokens}</div>
        <div className="rounded border p-3">总成本: {data.total_cost}</div>
        <div className="rounded border p-3">分组数: {data.items.length}</div>
        <div className="rounded border p-3">状态: {isLoading ? "加载中" : "已加载"}</div>
      </div>

      {!isLoading && !hasData ? (
        <div className="rounded border border-dashed p-6 text-sm text-muted-foreground">
          暂无用量数据
        </div>
      ) : (
        <div data-testid="usage-chart" className="h-72 rounded border p-3">
          <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={240}>
            <BarChart data={data.items}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="tokens" fill="#2563eb" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}