"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { TechniqueDetail } from "@/features/knowledge/types";
import { knowledgeApi } from "@/lib/api/knowledge";

interface SkillDetailProps {
  technique: TechniqueDetail;
  onPublish?: () => void;
  onEdit?: () => void;
}

const canPublish = (t: TechniqueDetail) =>
  (t.maturity === "draft" || t.maturity === "reviewed") && t.status !== "inactive";

export function SkillDetail({ technique, onPublish, onEdit }: SkillDetailProps) {
  const [showPublishConfirm, setShowPublishConfirm] = useState(false);
  const queryClient = useQueryClient();

  const publishMutation = useMutation({
    mutationFn: () => knowledgeApi.publishTechnique(technique.technique_id),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["knowledge", "techniques"],
      });
      setShowPublishConfirm(false);
      onPublish?.();
    },
  });

  return (
    <div className="space-y-6" data-testid="skill-detail">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-lg font-semibold">{technique.name}</h2>
          <p className="font-mono text-xs text-muted-foreground">
            {technique.skill_code}
          </p>
        </div>
        <div className="flex gap-2">
          {onEdit && (
            <button
              className="rounded border px-3 py-1 text-sm"
              onClick={onEdit}
            >
              编辑
            </button>
          )}
          {canPublish(technique) && (
            <button
              className="rounded bg-primary px-3 py-1 text-sm text-primary-foreground"
              onClick={() => setShowPublishConfirm(true)}
            >
              发布
            </button>
          )}
        </div>
      </div>

      {/* Publish confirm dialog */}
      {showPublishConfirm && (
        <div className="rounded border bg-card p-4 shadow">
          <p className="text-sm">确认发布技能「{technique.name}」？发布后状态变为 active。</p>
          <div className="mt-3 flex gap-2">
            <button
              className="rounded bg-primary px-3 py-1 text-sm text-primary-foreground disabled:opacity-50"
              disabled={publishMutation.isPending}
              onClick={() => publishMutation.mutate()}
            >
              确认发布
            </button>
            <button
              className="rounded border px-3 py-1 text-sm"
              onClick={() => setShowPublishConfirm(false)}
            >
              取消
            </button>
          </div>
          {publishMutation.error && (
            <p className="mt-2 text-sm text-destructive">
              {(publishMutation.error as Error).message}
            </p>
          )}
        </div>
      )}

      {/* Meta info */}
      <div className="grid grid-cols-2 gap-4 rounded border p-4 text-sm sm:grid-cols-4">
        <div>
          <span className="text-muted-foreground">分类</span>
          <p>{technique.category}</p>
        </div>
        <div>
          <span className="text-muted-foreground">层级</span>
          <p>{technique.layer}</p>
        </div>
        <div>
          <span className="text-muted-foreground">任务类型</span>
          <p>{technique.task_type}</p>
        </div>
        <div>
          <span className="text-muted-foreground">成熟度</span>
          <p>{technique.maturity}</p>
        </div>
      </div>

      {technique.summary && (
        <div>
          <h3 className="mb-1 font-medium">摘要</h3>
          <p className="text-sm text-muted-foreground">{technique.summary}</p>
        </div>
      )}

      {/* 条件 Condition */}
      <div>
        <h3 className="mb-2 font-medium">条件 (Conditions)</h3>
        {technique.conditions.length === 0 ? (
          <p className="text-sm text-muted-foreground">暂无条件定义</p>
        ) : (
          <ul className="space-y-1">
            {technique.conditions.map((c) => (
              <li key={c.condition_id} className="rounded border px-3 py-2 text-sm">
                {c.description}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* 动作 Action */}
      <div>
        <h3 className="mb-2 font-medium">动作 (Actions)</h3>
        {technique.actions.length === 0 ? (
          <p className="text-sm text-muted-foreground">暂无动作定义</p>
        ) : (
          <ul className="space-y-1">
            {technique.actions.map((a) => (
              <li key={a.action_id} className="rounded border px-3 py-2 text-sm">
                {a.description}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* 收益代价 Tradeoffs */}
      <div>
        <h3 className="mb-2 font-medium">收益与代价 (Tradeoffs)</h3>
        {technique.tradeoffs.length === 0 ? (
          <p className="text-sm text-muted-foreground">暂无收益代价数据</p>
        ) : (
          <ul className="space-y-1">
            {technique.tradeoffs.map((t) => (
              <li key={t.tradeoff_id} className="rounded border px-3 py-2 text-sm">
                <span className="font-medium">{t.dimension}</span>:{" "}
                {t.effect_direction}
                {t.notes && (
                  <span className="ml-2 text-muted-foreground">{t.notes}</span>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* 证据 Evidence */}
      <div>
        <h3 className="mb-2 font-medium">证据来源 (Evidence)</h3>
        {technique.evidences.length === 0 ? (
          <p className="text-sm text-muted-foreground">暂无证据记录</p>
        ) : (
          <ul className="space-y-1">
            {technique.evidences.map((e) => (
              <li key={e.evidence_id} className="rounded border px-3 py-2 text-sm">
                <span className="font-medium">{e.evidence_type}</span>
                {e.notes && (
                  <span className="ml-2 text-muted-foreground">{e.notes}</span>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div>
        <h3 className="mb-2 font-medium">关系 (Relations)</h3>
        {!technique.relations || technique.relations.length === 0 ? (
          <p className="text-sm text-muted-foreground">暂无关系记录</p>
        ) : (
          <ul className="space-y-1">
            {technique.relations.map((relation) => (
              <li
                key={relation.relation_id}
                className="rounded border px-3 py-2 text-sm"
              >
                <span className="font-medium">{relation.relation_type}</span>
                {relation.description && (
                  <span className="ml-2 text-muted-foreground">
                    {relation.description}
                  </span>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
