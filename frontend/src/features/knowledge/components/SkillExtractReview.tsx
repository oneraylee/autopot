"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { SkillCandidate } from "@/features/knowledge/types";
import { knowledgeApi } from "@/lib/api/knowledge";
import { SkillEditForm } from "./SkillEditForm";

interface SkillExtractReviewProps {
  documentId: string;
  candidates?: SkillCandidate[];
  onExtracted?: (candidates: SkillCandidate[]) => void;
}

export function SkillExtractReview({
  documentId,
  candidates: initialCandidates,
  onExtracted,
}: SkillExtractReviewProps) {
  const [candidates, setCandidates] = useState<SkillCandidate[]>(
    initialCandidates ?? [],
  );
  const [editingCandidate, setEditingCandidate] =
    useState<SkillCandidate | null>(null);
  const queryClient = useQueryClient();

  const extractMutation = useMutation({
    mutationFn: () => knowledgeApi.extractTechniques(documentId),
    onSuccess: (res) => {
      const nextCandidates = Array.isArray(res.candidates) ? res.candidates : [];
      setCandidates(nextCandidates);
      onExtracted?.(nextCandidates);
    },
  });

  const confirmMutation = useMutation({
    mutationFn: (candidate: SkillCandidate) =>
      knowledgeApi.createTechnique({
        skill_code: `${candidate.category}.${candidate.layer}.${candidate.name
          .toLowerCase()
          .replace(/\s+/g, "_")}`,
        name: candidate.name,
        category: candidate.category,
        layer: candidate.layer,
        task_type: "det",
        summary: `${candidate.condition} → ${candidate.action}`,
      }),
    onSuccess: (_, candidate) => {
      queryClient.invalidateQueries({ queryKey: ["knowledge", "techniques"] });
      setCandidates((prev) =>
        prev.filter((c) => c.candidate_id !== candidate.candidate_id),
      );
    },
  });

  const normalizedCandidates = Array.isArray(candidates) ? candidates : [];

  function handleReject(candidateId: string) {
    setCandidates((prev) => prev.filter((c) => c.candidate_id !== candidateId));
  }

  if (editingCandidate) {
    return (
      <div className="space-y-4">
        <h3 className="font-medium">修改候选技能</h3>
        <SkillEditForm
          defaultValues={{
            name: editingCandidate.name,
            category: editingCandidate.category,
            layer: editingCandidate.layer,
            task_type: "det",
            skill_code: `${editingCandidate.category}.${editingCandidate.layer}.${editingCandidate.name
              .toLowerCase()
              .replace(/\s+/g, "_")}`,
          }}
          onSuccess={() => {
            setCandidates((prev) =>
              prev.filter((c) => c.candidate_id !== editingCandidate.candidate_id),
            );
            setEditingCandidate(null);
          }}
        />
        <button
          className="text-sm text-muted-foreground underline"
          onClick={() => setEditingCandidate(null)}
        >
          返回
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="skill-extract-review">
      <div className="flex items-center gap-3">
        <button
          data-testid="extract-skills-btn"
          className="rounded bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50"
          disabled={extractMutation.isPending}
          onClick={() => extractMutation.mutate()}
        >
          {extractMutation.isPending ? "抽取中..." : "抽取技能"}
        </button>
        {extractMutation.error && (
          <p className="text-sm text-destructive">
            {(extractMutation.error as Error).message}
          </p>
        )}
      </div>

      {normalizedCandidates.length === 0 && (
        <p className="text-sm text-muted-foreground">暂无候选技能，点击「抽取技能」开始</p>
      )}

      {normalizedCandidates.map((candidate) => (
        <div
          key={candidate.candidate_id}
          className="rounded border p-4 text-sm"
          data-testid="candidate-item"
        >
          <div className="mb-2 flex items-start justify-between gap-2">
            <div>
              <p className="font-medium">{candidate.name}</p>
              <p className="text-muted-foreground">
                {candidate.category} / {candidate.layer}
              </p>
            </div>
            <div className="flex gap-2 shrink-0">
              <button
                data-testid={`candidate-confirm-btn-${candidate.candidate_id}`}
                className="rounded bg-green-600 px-3 py-1 text-xs text-white disabled:opacity-50"
                disabled={confirmMutation.isPending}
                onClick={() => confirmMutation.mutate(candidate)}
              >
                确认
              </button>
              <button
                className="rounded border px-3 py-1 text-xs"
                onClick={() => setEditingCandidate(candidate)}
              >
                修改
              </button>
              <button
                className="rounded border border-destructive px-3 py-1 text-xs text-destructive"
                onClick={() => handleReject(candidate.candidate_id)}
              >
                拒绝
              </button>
            </div>
          </div>
          <div className="space-y-1 text-muted-foreground">
            <p>
              <span className="font-medium text-foreground">条件：</span>
              {candidate.condition}
            </p>
            <p>
              <span className="font-medium text-foreground">动作：</span>
              {candidate.action}
            </p>
            <p>
              <span className="font-medium text-foreground">代价：</span>
              {candidate.tradeoff}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
