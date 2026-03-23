"use client";

import type { LogPage } from "@/lib/api/job";

interface LogViewerProps {
  data: LogPage | undefined;
  isLoading: boolean;
  page: number;
  onPageChange: (page: number) => void;
}

export function LogViewer({ data, isLoading, page, onPageChange }: LogViewerProps) {
  if (isLoading) {
    return <div className="p-4">加载日志中...</div>;
  }

  if (!data || data.items.length === 0) {
    return <div className="p-4 text-muted-foreground">暂无日志</div>;
  }

  const totalPages = Math.ceil(data.total / data.page_size);

  return (
    <div className="space-y-4">
      <div className="rounded-lg border bg-muted/50 p-4 font-mono text-sm">
        {data.items.map((entry) => (
          <div key={entry.line} className="py-0.5">
            <span className="mr-4 text-muted-foreground">{entry.line}</span>
            {entry.message}
          </div>
        ))}
      </div>
      <div className="flex items-center gap-2">
        <button
          className="rounded border px-3 py-1 text-sm disabled:opacity-50"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          上一页
        </button>
        <span className="text-sm text-muted-foreground">
          {page} / {totalPages}
        </span>
        <button
          className="rounded border px-3 py-1 text-sm disabled:opacity-50"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          下一页
        </button>
      </div>
    </div>
  );
}
