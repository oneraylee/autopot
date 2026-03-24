"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import type { ConflictPair, ArbitrationVerdict } from "@/features/knowledge/types";
import { knowledgeApi } from "@/lib/api/knowledge";

interface ConflictArbitrationProps {
  conflicts: ConflictPair[];
  onResolved?: (conflictId: string) => void;
}

const VERDICT_LABELS: Record<ArbitrationVerdict, string> = {
  keep_a: "保A",
  keep_b: "保B",
  split_condition: "条件分流",
  mark_experiment: "标记需实验验证",
};

export function ConflictArbitration({
  conflicts,
  onResolved,
}: ConflictArbitrationProps) {
  const [selections, setSelections] = useState<
    Record<string, ArbitrationVerdict>
  >({});

  const resolveMutation = useMutation({
    mutationFn: ({
      conflict,
      verdict,
    }: {
      conflict: ConflictPair;
      verdict: ArbitrationVerdict;
    }) =>
      knowledgeApi.resolveConflicts({
        conflict_id: conflict.conflict_id,
        verdict,
        technique_ids: [
          conflict.technique_a.technique_id,
          conflict.technique_b.technique_id,
        ],
      }),
    onSuccess: (_, { conflict }) => {
      onResolved?.(conflict.conflict_id);
    },
  });

  if (conflicts.length === 0) {
    return <div className="p-4 text-muted-foreground">暂无冲突需要仲裁</div>;
  }

  return (
    <div className="space-y-6" data-testid="conflict-arbitration">
      {conflicts.map((conflict) => (
        <div
          key={conflict.conflict_id}
          className="rounded border p-4"
          data-testid="conflict-pair"
        >
          {/* 冲突类型 */}
          <div className="mb-3 flex items-center gap-2 text-sm">
            <span className="rounded bg-destructive/10 px-2 py-0.5 text-xs text-destructive">
              {conflict.conflict_type}
            </span>
          </div>

          {/* 两条技能对比 */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="rounded border p-3">
              <p className="font-medium">{conflict.technique_a.name}</p>
              <p className="text-muted-foreground">{conflict.technique_a.summary}</p>
            </div>
            <div className="rounded border p-3">
              <p className="font-medium">{conflict.technique_b.name}</p>
              <p className="text-muted-foreground">{conflict.technique_b.summary}</p>
            </div>
          </div>

          {/* LLM 建议 */}
          {conflict.llm_suggestion && (
            <div className="mt-3 rounded bg-muted p-3 text-sm text-muted-foreground">
              <span className="font-medium text-foreground">LLM 建议：</span>
              {conflict.llm_suggestion}
            </div>
          )}

          {/* 仲裁选项 */}
          <div className="mt-4">
            <p className="mb-2 text-sm font-medium">仲裁选项</p>
            <div className="flex flex-wrap gap-2">
              {(
                Object.entries(VERDICT_LABELS) as [ArbitrationVerdict, string][]
              ).map(([verdict, label]) => (
                <button
                  key={verdict}
                  className={`rounded border px-3 py-1 text-sm transition-colors ${
                    selections[conflict.conflict_id] === verdict
                      ? "border-primary bg-primary text-primary-foreground"
                      : "hover:bg-accent"
                  }`}
                  onClick={() =>
                    setSelections((prev) => ({
                      ...prev,
                      [conflict.conflict_id]: verdict,
                    }))
                  }
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* 提交 */}
          <div className="mt-3 flex items-center gap-2">
            <button
              className="rounded bg-primary px-4 py-1.5 text-sm text-primary-foreground disabled:opacity-50"
              disabled={
                !selections[conflict.conflict_id] ||
                resolveMutation.isPending
              }
              onClick={() => {
                const verdict = selections[conflict.conflict_id];
                if (verdict) {
                  resolveMutation.mutate({ conflict, verdict });
                }
              }}
            >
              确认仲裁
            </button>
            {resolveMutation.error && (
              <p className="text-sm text-destructive">
                {(resolveMutation.error as Error).message}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
