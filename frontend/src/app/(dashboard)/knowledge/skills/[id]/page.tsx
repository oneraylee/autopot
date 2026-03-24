"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { knowledgeApi } from "@/lib/api/knowledge";
import { QueryState } from "@/components/QueryState";
import { SkillDetail } from "@/features/knowledge/components/SkillDetail";
import { SkillEditForm } from "@/features/knowledge/components/SkillEditForm";

interface SkillDetailPageProps {
  params: { id: string };
}

export default function SkillDetailPage({ params }: SkillDetailPageProps) {
  const [isEditing, setIsEditing] = useState(false);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["knowledge", "techniques", params.id],
    queryFn: () => knowledgeApi.getTechnique(params.id),
  });

  const { data: relationsData } = useQuery({
    queryKey: ["knowledge", "techniques", params.id, "relations"],
    queryFn: () => knowledgeApi.getTechniqueRelations(params.id),
    enabled: !!data,
  });

  const technique =
    data === undefined
      ? undefined
      : {
          ...data,
          relations: relationsData?.items ?? data.relations ?? [],
        };

  return (
    <div>
      <QueryState
        isLoading={isLoading}
        error={error as Error | null}
        onRetry={() => refetch()}
      >
        {technique && !isEditing && (
          <SkillDetail
            technique={technique}
            onEdit={() => setIsEditing(true)}
            onPublish={() => refetch()}
          />
        )}

        {technique && isEditing && (
          <div>
            <h2 className="mb-4 text-lg font-semibold">编辑技能</h2>
            <SkillEditForm
              techniqueId={params.id}
              defaultValues={{
                skill_code: technique.skill_code,
                name: technique.name,
                category: technique.category,
                layer: technique.layer,
                task_type: technique.task_type,
                summary: technique.summary,
              }}
              onSuccess={() => {
                setIsEditing(false);
                refetch();
              }}
            />
            <button
              className="mt-3 text-sm text-muted-foreground underline"
              onClick={() => setIsEditing(false)}
            >
              取消
            </button>
          </div>
        )}
      </QueryState>
    </div>
  );
}
