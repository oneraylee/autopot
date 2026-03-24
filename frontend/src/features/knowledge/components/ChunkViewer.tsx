import type { KnowledgeChunk } from "@/features/knowledge/types";

interface ChunkViewerProps {
  chunks: Pick<KnowledgeChunk, "chunk_id" | "section_path" | "token_count" | "keywords">[];
}

export function ChunkViewer({ chunks }: ChunkViewerProps) {
  if (chunks.length === 0) {
    return <div className="p-4 text-muted-foreground">暂无切片数据</div>;
  }

  return (
    <div className="space-y-3" data-testid="chunk-viewer">
      {chunks.map((chunk) => (
        <div
          key={chunk.chunk_id}
          className="rounded border p-3 text-sm"
          data-testid="chunk-item"
        >
          <div className="flex items-center justify-between">
            <span className="font-medium">{chunk.section_path}</span>
            <span className="text-muted-foreground">
              <span data-testid="token-count">{chunk.token_count}</span> tokens
            </span>
          </div>
          {chunk.keywords.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {chunk.keywords.map((kw) => (
                <span
                  key={kw}
                  className="rounded bg-muted px-2 py-0.5 text-xs"
                >
                  {kw}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
