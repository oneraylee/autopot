"use client";

import { useState } from "react";
import Link from "next/link";
import { useJobList } from "@/features/job/hooks/useJobList";
import { CreateJobForm } from "@/features/job/components/CreateJobForm";

const statusColors: Record<string, string> = {
  created: "bg-gray-200 text-gray-800",
  queued: "bg-yellow-100 text-yellow-800",
  running: "bg-blue-100 text-blue-800",
  succeeded: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
  canceled: "bg-gray-300 text-gray-700",
  evaluating: "bg-purple-100 text-purple-800",
  eval_succeeded: "bg-green-100 text-green-800",
  eval_failed: "bg-red-100 text-red-800",
  evidence_ready: "bg-indigo-100 text-indigo-800",
  llm_analyzing: "bg-purple-100 text-purple-800",
  llm_done: "bg-green-100 text-green-800",
  llm_failed: "bg-red-100 text-red-800",
};

export default function JobsPage() {
  const { data, isLoading, error } = useJobList();
  const [showCreate, setShowCreate] = useState(false);

  if (isLoading) return <div className="p-6">加载中...</div>;
  if (error) return <div className="p-6 text-destructive">错误: {error.message}</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">任务列表</h1>
        <button
          type="button"
          className="rounded bg-primary px-4 py-2 text-sm text-primary-foreground"
          onClick={() => setShowCreate((v) => !v)}
        >
          创建任务
        </button>
      </div>

      {showCreate && <CreateJobForm />}

      {!data || data.length === 0 ? (
        <div className="text-muted-foreground">暂无任务</div>
      ) : (
        <div className="rounded-lg border">
          <table className="w-full text-sm" data-testid="job-table">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="p-3 text-left">Job ID</th>
                <th className="p-3 text-left">类型</th>
                <th className="p-3 text-left">状态</th>
                <th className="p-3 text-left">更新时间</th>
              </tr>
            </thead>
            <tbody>
              {data.map((job) => (
                <tr key={job.job_id} className="border-b hover:bg-muted/30">
                  <td className="p-3">
                    <Link href={`/jobs/${job.job_id}`} className="text-primary underline">
                      {job.job_id}
                    </Link>
                  </td>
                  <td className="p-3">{job.task_type}</td>
                  <td className="p-3">
                    <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${statusColors[job.status] ?? ""}`}>
                      {job.status}
                    </span>
                  </td>
                  <td className="p-3">{new Date(job.updated_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
