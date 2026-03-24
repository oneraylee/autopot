"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { DocumentImportForm } from "@/features/knowledge/components/DocumentImportForm";
import { DocumentList } from "@/features/knowledge/components/DocumentList";
import { ChunkViewer } from "@/features/knowledge/components/ChunkViewer";
import { useQuery } from "@tanstack/react-query";
import { knowledgeApi } from "@/lib/api/knowledge";

export default function KnowledgeDocumentsPage() {
  const searchParams = useSearchParams();
  const sourceId = searchParams.get("source_id") ?? "";
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [showImport, setShowImport] = useState(false);

  const { data: chunksData } = useQuery({
    queryKey: ["knowledge", "chunks", selectedDocId],
    queryFn: () => knowledgeApi.getChunks(selectedDocId!),
    enabled: !!selectedDocId,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">文档导入</h1>
        {sourceId && (
          <button
            data-testid="knowledge-doc-toggle-import"
            className="rounded bg-primary px-4 py-2 text-sm text-primary-foreground"
            onClick={() => setShowImport((v) => !v)}
          >
            {showImport ? "收起" : "导入文档"}
          </button>
        )}
      </div>

      {!sourceId && (
        <p className="text-muted-foreground">请先选择知识来源（source_id 必须在 URL 中提供）</p>
      )}

      {sourceId && showImport && (
        <div className="rounded border p-4">
          <h2 className="mb-3 font-medium">导入新文档</h2>
          <DocumentImportForm
            sourceId={sourceId}
            onSuccess={() => setShowImport(false)}
          />
        </div>
      )}

      {sourceId && (
        <div>
          <h2 className="mb-2 font-medium">文档列表</h2>
          <DocumentList sourceId={sourceId} onSelect={setSelectedDocId} />
        </div>
      )}

      {selectedDocId && (
        <div>
          <h2 className="mb-2 font-medium">切片预览</h2>
          <ChunkViewer chunks={chunksData?.items ?? []} />
        </div>
      )}
    </div>
  );
}
