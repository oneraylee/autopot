"use client";

import { useQuery } from "@tanstack/react-query";
import { knowledgeApi } from "@/lib/api/knowledge";
import type { ParseStatus } from "@/features/knowledge/types";

const STATUS_LABEL: Record<ParseStatus, string> = {
  pending: "解析中",
  parsed: "已解析",
  failed: "失败",
};

interface DocumentListProps {
  sourceId: string;
  onSelect?: (documentId: string) => void;
}

export function DocumentList({ sourceId, onSelect }: DocumentListProps) {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["knowledge", "documents", sourceId],
    queryFn: () =>
      // Reuse listSources pattern — fetch all docs filtered by sourceId
      // Backend: GET /knowledge/documents/{document_id} doesn't list by source;
      // for now we use source placeholder until a list endpoint is available.
      knowledgeApi.getDocument(sourceId).then((doc) => ({ items: [doc] })),
    enabled: !!sourceId,
    refetchInterval: (query) => {
      const docs = query.state.data?.items ?? [];
      const hasPending = docs.some((d) => d.parse_status === "pending");
      return hasPending ? 3000 : false;
    },
  });

  if (isLoading) {
    return <div className="p-4 text-muted-foreground">加载中...</div>;
  }
  if (error) {
    return (
      <div className="p-4">
        <p className="text-destructive">{(error as Error).message}</p>
        <button
          className="mt-2 rounded border px-3 py-1 text-sm"
          onClick={() => refetch()}
        >
          重试
        </button>
      </div>
    );
  }

  const docs = data?.items ?? [];
  if (docs.length === 0) {
    return <div className="p-4 text-muted-foreground">暂无文档</div>;
  }

  return (
    <div className="overflow-x-auto" data-testid="document-list">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-muted-foreground">
            <th className="px-4 py-2">标题</th>
            <th className="px-4 py-2">类型</th>
            <th className="px-4 py-2">解析状态</th>
          </tr>
        </thead>
        <tbody>
          {docs.map((doc) => (
            <tr
              key={doc.document_id}
              data-testid={`document-row-${doc.document_id}`}
              className="cursor-pointer border-b hover:bg-accent/50"
              onClick={() => onSelect?.(doc.document_id)}
            >
              <td className="px-4 py-2 font-medium">{doc.title}</td>
              <td className="px-4 py-2">{doc.doc_type}</td>
              <td className="px-4 py-2">
                <span
                  className={
                    doc.parse_status === "parsed"
                      ? "text-green-600"
                      : doc.parse_status === "failed"
                        ? "text-destructive"
                        : "text-muted-foreground"
                  }
                >
                  {STATUS_LABEL[doc.parse_status] ?? doc.parse_status}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
