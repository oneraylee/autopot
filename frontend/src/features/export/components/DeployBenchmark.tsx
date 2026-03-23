"use client";

import { useQuery } from "@tanstack/react-query";
import { getDeployBenchmark, type DeployBenchmark } from "@/lib/api/export";

interface DeployBenchmarkViewProps {
  exportId: string;
}

export function DeployBenchmarkView({ exportId }: DeployBenchmarkViewProps) {
  const { data, isLoading, error } = useQuery<DeployBenchmark>({
    queryKey: ["deploy-benchmark", exportId],
    queryFn: () => getDeployBenchmark(exportId),
  });

  if (isLoading) return <p className="text-sm text-muted-foreground">加载中...</p>;
  if (error) return <p className="text-sm text-destructive">暂无基准数据</p>;
  if (!data) return null;

  return (
    <div className="space-y-3">
      <h3 className="text-lg font-semibold">部署基准</h3>
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b">
            <th className="text-left py-1">指标</th>
            <th className="text-right py-1">值</th>
          </tr>
        </thead>
        <tbody>
          <tr className="border-b">
            <td className="py-1">时延 P95 (ms)</td>
            <td className="text-right py-1">{data.latency_ms}</td>
          </tr>
          <tr className="border-b">
            <td className="py-1">吞吐 (FPS)</td>
            <td className="text-right py-1">{data.throughput_fps}</td>
          </tr>
          <tr className="border-b">
            <td className="py-1">显存 (MB)</td>
            <td className="text-right py-1">{data.memory_mb}</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
