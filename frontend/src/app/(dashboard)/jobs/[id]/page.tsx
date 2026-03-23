"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useJob } from "@/features/job/hooks/useJob";
import { useJobLogs } from "@/features/job/hooks/useJobLogs";
import { useJobMetrics } from "@/features/job/hooks/useJobMetrics";
import { LogViewer } from "@/features/job/components/LogViewer";
import { MetricsChart } from "@/features/job/components/MetricsChart";
import { ArtifactTabs } from "@/features/job/components/ArtifactTabs";
import { StartJobButton } from "@/features/job/components/StartJobButton";
import { useJobArtifacts } from "@/features/job/hooks/useJobArtifacts";

const statusColors: Record<string, string> = {
  created: "bg-gray-200 text-gray-800",
  queued: "bg-yellow-100 text-yellow-800",
  running: "bg-blue-100 text-blue-800",
  succeeded: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
};

type TabKey = "logs" | "metrics" | "artifacts";

export default function JobDetailPage() {
  const params = useParams<{ id: string }>();
  const jobId = params.id;
  const [tab, setTab] = useState<TabKey>("logs");
  const [logPage, setLogPage] = useState(1);

  const { data: job, isLoading, error } = useJob(jobId);
  const logs = useJobLogs(jobId, logPage, 20);
  const metrics = useJobMetrics(jobId, 0, Date.now());
  const artifacts = useJobArtifacts(jobId);

  if (isLoading) return <div className="p-6">加载中...</div>;
  if (error) return <div className="p-6 text-destructive">错误: {error.message}</div>;
  if (!job) return <div className="p-6 text-muted-foreground">任务不存在</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold">{job.job_id}</h1>
        <span className={`rounded px-2 py-0.5 text-xs font-medium ${statusColors[job.status] ?? "bg-gray-200"}`}>
          {job.status}
        </span>
      </div>

      <StartJobButton jobId={jobId} status={job.status} />

      <div className="grid grid-cols-3 gap-4">
        <div className="rounded-lg border p-4">
          <div className="text-sm text-muted-foreground">类型</div>
          <div className="font-medium">{job.task_type}</div>
        </div>
        <div className="rounded-lg border p-4">
          <div className="text-sm text-muted-foreground">数据集版本</div>
          <div className="font-medium">{job.dataset_version_id}</div>
        </div>
        <div className="rounded-lg border p-4">
          <div className="text-sm text-muted-foreground">创建时间</div>
          <div className="font-medium">{new Date(job.created_at).toLocaleString()}</div>
        </div>
      </div>

      <div className="flex gap-2 border-b">
        <button
          className={`px-4 py-2 text-sm font-medium ${tab === "logs" ? "border-b-2 border-primary text-primary" : "text-muted-foreground"}`}
          onClick={() => setTab("logs")}
        >
          日志
        </button>
        <button
          className={`px-4 py-2 text-sm font-medium ${tab === "metrics" ? "border-b-2 border-primary text-primary" : "text-muted-foreground"}`}
          onClick={() => setTab("metrics")}
        >
          指标
        </button>
        <button
          className={`px-4 py-2 text-sm font-medium ${tab === "artifacts" ? "border-b-2 border-primary text-primary" : "text-muted-foreground"}`}
          onClick={() => setTab("artifacts")}
        >
          产物
        </button>
      </div>

      {tab === "logs" && (
        <LogViewer data={logs.data} isLoading={logs.isLoading} page={logPage} onPageChange={setLogPage} />
      )}
      {tab === "metrics" && (
        <MetricsChart data={metrics.data} isLoading={metrics.isLoading} />
      )}
      {tab === "artifacts" && (
        <ArtifactTabs jobId={jobId} artifacts={artifacts.data} />
      )}
    </div>
  );
}
