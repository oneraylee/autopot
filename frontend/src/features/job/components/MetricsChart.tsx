"use client";

import type { MetricsResult } from "@/lib/api/job";

interface MetricsChartProps {
  data: MetricsResult | undefined;
  isLoading: boolean;
}

export function MetricsChart({ data, isLoading }: MetricsChartProps) {
  if (isLoading) {
    return <div className="p-4">加载指标中...</div>;
  }

  if (!data || data.items.length === 0) {
    return <div className="p-4 text-muted-foreground">暂无指标数据</div>;
  }

  const metricKeys = Object.keys(data.items[0]?.values ?? {});

  return (
    <div className="space-y-4">
      <div className="rounded-lg border p-4">
        <table className="w-full text-sm" data-testid="metrics-table">
          <thead>
            <tr className="border-b">
              <th className="py-2 text-left">时间戳</th>
              {metricKeys.map((key) => (
                <th key={key} className="py-2 text-left">{key}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.items.map((point) => (
              <tr key={point.ts} className="border-b">
                <td className="py-2">{new Date(point.ts * 1000).toLocaleString()}</td>
                {metricKeys.map((key) => (
                  <td key={key} className="py-2">{point.values[key]?.toFixed(4)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
