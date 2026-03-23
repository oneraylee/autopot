"use client";

import { useQuery } from "@tanstack/react-query";
import { getExportStatus, type ExportTask } from "@/lib/api/export";

interface ExportStatusProps {
  exportId: string;
}

const terminalStatuses = new Set(["succeeded", "failed"]);

export function ExportStatus({ exportId }: ExportStatusProps) {
  const { data, isLoading, error } = useQuery<ExportTask>({
    queryKey: ["export-status", exportId],
    queryFn: () => getExportStatus(exportId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status && terminalStatuses.has(status)) return false;
      return 5000;
    },
  });

  if (isLoading) return <p className="text-sm text-muted-foreground">加载中...</p>;
  if (error) return <p className="text-sm text-destructive">错误: {error.message}</p>;
  if (!data) return null;

  const statusColor =
    data.status === "succeeded"
      ? "bg-green-100 text-green-800"
      : data.status === "failed"
        ? "bg-red-100 text-red-800"
        : "bg-blue-100 text-blue-800";

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium">导出状态</span>
        <span className={`rounded px-2 py-0.5 text-xs font-medium ${statusColor}`}>
          {data.status}
        </span>
      </div>
      <table className="w-full text-sm border-collapse">
        <tbody>
          <tr className="border-b">
            <td className="py-1 text-muted-foreground">Export ID</td>
            <td className="py-1 font-mono">{data.export_id}</td>
          </tr>
          <tr className="border-b">
            <td className="py-1 text-muted-foreground">Job ID</td>
            <td className="py-1 font-mono">{data.job_id}</td>
          </tr>
          <tr className="border-b">
            <td className="py-1 text-muted-foreground">Backend</td>
            <td className="py-1">{data.backend}</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
