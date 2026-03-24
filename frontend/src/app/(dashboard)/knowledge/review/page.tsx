"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { QueryState } from "@/components/QueryState";
import { SkillExtractReview } from "@/features/knowledge/components/SkillExtractReview";
import { ConflictArbitration } from "@/features/knowledge/components/ConflictArbitration";
import type { KnowledgeDocument } from "@/features/knowledge/types";

type Tab = "review" | "conflicts";

export default function KnowledgeReviewPage() {
  const searchParams = useSearchParams();
  const [activeTab, setActiveTab] = useState<Tab>("review");
  const [selectedDocId, setSelectedDocId] = useState<string>(
    searchParams.get("doc_id") ?? "",
  );
  const shouldLoadDocumentOptions = selectedDocId.length === 0;

  // For demo/review: list documents using a placeholder source query
  // In production this would list all parsed documents across sources
  const { data: docData, isLoading: docLoading, error: docError } = useQuery({
    queryKey: ["knowledge", "review", "docs"],
    enabled: shouldLoadDocumentOptions,
    queryFn: () =>
      // Using a generic fetch of documents placeholder — real implementation
      // would have a dedicated list endpoint
      Promise.resolve({ items: [] as KnowledgeDocument[] }),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">技能审核</h1>

      {/* Tabs */}
      <div className="flex border-b">
        {(["review", "conflicts"] as Tab[]).map((tab) => (
          <button
            key={tab}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === tab
                ? "border-b-2 border-primary text-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
            onClick={() => setActiveTab(tab)}
          >
            {tab === "review" ? "抽取审核" : "冲突仲裁"}
          </button>
        ))}
      </div>

      {activeTab === "review" && (
        <div className="space-y-4">
          <div>
            <label htmlFor="doc-select" className="block text-sm font-medium">
              选择文档
            </label>
            {selectedDocId ? (
              <p className="mt-1 text-sm text-muted-foreground" data-testid="review-selected-doc">
                当前文档: {selectedDocId}
              </p>
            ) : (
              <QueryState
                isLoading={docLoading}
                error={docError as Error | null}
                isEmpty={(docData?.items ?? []).length === 0}
                emptyMessage="暂无已导入文档，请先在「文档导入」页导入文档"
              >
                <select
                  id="doc-select"
                  className="mt-1 rounded border px-3 py-2 text-sm"
                  value={selectedDocId}
                  onChange={(e) => setSelectedDocId(e.target.value)}
                >
                  <option value="">-- 请选择 --</option>
                  {(docData?.items ?? []).map((doc) => (
                    <option key={doc.document_id} value={doc.document_id}>
                      {doc.title}
                    </option>
                  ))}
                </select>
              </QueryState>
            )}
          </div>

          {selectedDocId && (
            <SkillExtractReview documentId={selectedDocId} />
          )}
        </div>
      )}

      {activeTab === "conflicts" && (
        <ConflictArbitration conflicts={[]} />
      )}
    </div>
  );
}
