import type { CallLogParams, CallLogResponse } from "@/lib/api/llm-gateway";

interface CallLogListProps {
  data: CallLogResponse;
  onPageChange: (page: number) => void;
  onFilterChange: (filters: Partial<CallLogParams>) => void;
  isLoading: boolean;
}

export function CallLogList({ data, onPageChange, onFilterChange, isLoading }: CallLogListProps) {
  const totalPages = Math.max(1, Math.ceil(data.total / data.page_size));

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <select data-testid="filter-call-type" className="rounded border px-3 py-2 text-sm" onChange={(event) => onFilterChange({ call_type: event.target.value || undefined })}>
          <option value="">全部调用</option>
          <option value="agent_plan">规划调用</option>
          <option value="skill_extract">技能抽取</option>
        </select>
        <select data-testid="filter-provider" className="rounded border px-3 py-2 text-sm" onChange={(event) => onFilterChange({ provider: event.target.value || undefined })}>
          <option value="">全部服务商</option>
          <option value="openai">OpenAI</option>
        </select>
        <select data-testid="filter-status" className="rounded border px-3 py-2 text-sm" onChange={(event) => onFilterChange({ status: event.target.value || undefined })}>
          <option value="">全部结果</option>
          <option value="success">成功</option>
          <option value="failed">失败</option>
        </select>
      </div>

      {data.items.length === 0 && !isLoading ? (
        <div className="p-6 text-muted-foreground">暂无调用日志</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-muted-foreground">
                <th className="px-4 py-2">调用类型</th>
                <th className="px-4 py-2">Provider</th>
                <th className="px-4 py-2">Model</th>
                <th className="px-4 py-2">Tokens</th>
                <th className="px-4 py-2">Latency</th>
                <th className="px-4 py-2">Cost</th>
                <th className="px-4 py-2">Status</th>
                <th className="px-4 py-2">Time</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((log) => (
                <tr
                  key={log.id}
                  data-testid={`call-log-row-${log.id}`}
                  className={`border-b ${log.status === "failed" ? "bg-red-50 text-red-700" : ""}`}
                >
                  <td className="px-4 py-2">{log.call_type}</td>
                  <td className="px-4 py-2">{log.provider}</td>
                  <td className="px-4 py-2">{log.model}</td>
                  <td className="px-4 py-2">{log.input_tokens + log.output_tokens}</td>
                  <td className="px-4 py-2">{log.latency_ms}</td>
                  <td className="px-4 py-2">{log.cost}</td>
                  <td className="px-4 py-2">{log.status}</td>
                  <td className="px-4 py-2">{log.created_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">第 {data.page} / {totalPages} 页</span>
        <button
          data-testid="call-log-next-page"
          className="rounded border px-3 py-2 text-sm"
          onClick={() => onPageChange(data.page + 1)}
          disabled={data.page >= totalPages}
        >
          下一页
        </button>
      </div>
    </div>
  );
}