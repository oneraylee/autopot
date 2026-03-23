"use client";

import { useParams } from "next/navigation";
import { useKpiConfig } from "@/features/project/hooks/useKpiConfig";

export default function KpiConfigPage() {
  const params = useParams<{ id: string }>();
  const { data, isLoading, error } = useKpiConfig(params.id);

  if (isLoading) {
    return <div className="p-6">加载中...</div>;
  }

  if (error) {
    return (
      <div className="p-6 text-destructive">
        错误: {error.message}
      </div>
    );
  }

  if (!data) {
    return <div className="p-6 text-muted-foreground">暂无数据</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">KPI 配置</h1>

      <div className="rounded-lg border p-4">
        <h2 className="mb-2 text-lg font-semibold">主要指标</h2>
        <p>{data.primary_kpi}</p>
      </div>

      <div className="rounded-lg border p-4">
        <h2 className="mb-2 text-lg font-semibold">阈值</h2>
        <p>{data.threshold}</p>
      </div>

      <div className="rounded-lg border p-4">
        <h2 className="mb-2 text-lg font-semibold">权重</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <span className="text-muted-foreground">Eval: </span>
            {data.weights.eval}
          </div>
          <div>
            <span className="text-muted-foreground">Deploy: </span>
            {data.weights.deploy}
          </div>
        </div>
      </div>

      <div className="rounded-lg border p-4">
        <h2 className="mb-2 text-lg font-semibold">部署约束</h2>
        {data.deploy_constraints.length === 0 ? (
          <p className="text-muted-foreground">无约束条件</p>
        ) : (
          <ul className="space-y-1">
            {data.deploy_constraints.map((c, i) => (
              <li key={i}>
                {c.metric} {c.operator} {c.value}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
