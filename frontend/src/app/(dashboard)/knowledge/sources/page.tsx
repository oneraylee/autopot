"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { knowledgeApi } from "@/lib/api/knowledge";
import { QueryState } from "@/components/QueryState";
import { SourceList } from "@/features/knowledge/components/SourceList";
import { CreateSourceForm } from "@/features/knowledge/components/CreateSourceForm";

export default function KnowledgeSourcesPage() {
  const [showForm, setShowForm] = useState(false);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["knowledge", "sources"],
    queryFn: knowledgeApi.listSources,
  });

  const sources = data?.items ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">知识来源</h1>
        <button
          data-testid="knowledge-source-toggle"
          className="rounded bg-primary px-4 py-2 text-sm text-primary-foreground"
          onClick={() => setShowForm((v) => !v)}
        >
          {showForm ? "收起" : "注册新来源"}
        </button>
      </div>

      {showForm && (
        <div className="rounded border p-4">
          <h2 className="mb-3 font-medium">注册知识来源</h2>
          <CreateSourceForm onSuccess={() => setShowForm(false)} />
        </div>
      )}

      <QueryState
        isLoading={isLoading}
        error={error as Error | null}
        isEmpty={sources.length === 0}
        emptyMessage="暂无知识来源，请先注册来源"
        onRetry={() => refetch()}
      >
        <SourceList sources={sources} />
      </QueryState>
    </div>
  );
}
