import type { KnowledgeSource } from "@/features/knowledge/types";

interface SourceListProps {
  sources: KnowledgeSource[];
}

export function SourceList({ sources }: SourceListProps) {
  if (sources.length === 0) {
    return (
      <div className="p-6 text-muted-foreground" data-testid="source-list-empty">
        暂无知识来源
      </div>
    );
  }

  return (
    <div className="overflow-x-auto" data-testid="source-list">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-muted-foreground">
            <th className="px-4 py-2">名称</th>
            <th className="px-4 py-2">类型</th>
            <th className="px-4 py-2">URI</th>
            <th className="px-4 py-2">信任等级</th>
            <th className="px-4 py-2">状态</th>
          </tr>
        </thead>
        <tbody>
          {sources.map((s) => (
            <tr key={s.source_id} className="border-b hover:bg-accent/50">
              <td className="px-4 py-2 font-medium">{s.name}</td>
              <td className="px-4 py-2">{s.source_type}</td>
              <td className="px-4 py-2 max-w-xs truncate text-muted-foreground">
                {s.uri}
              </td>
              <td className="px-4 py-2">{s.trust_level}</td>
              <td className="px-4 py-2">{s.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
