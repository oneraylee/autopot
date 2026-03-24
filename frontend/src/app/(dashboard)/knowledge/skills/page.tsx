"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { knowledgeApi } from "@/lib/api/knowledge";
import { QueryState } from "@/components/QueryState";
import { SkillList } from "@/features/knowledge/components/SkillList";
import { SkillTaxonomy } from "@/features/knowledge/components/SkillTaxonomy";
import type { TechniqueFilters, SkillCategory } from "@/features/knowledge/types";

export default function KnowledgeSkillsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const filters: TechniqueFilters = {
    category: (searchParams.get("category") as SkillCategory) || undefined,
    layer: searchParams.get("layer") || undefined,
    task_type: (searchParams.get("task_type") as TechniqueFilters["task_type"]) || undefined,
    maturity: (searchParams.get("maturity") as TechniqueFilters["maturity"]) || undefined,
  };

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["knowledge", "techniques", filters],
    queryFn: () => knowledgeApi.listTechniques(filters),
  });

  function updateFilters(next: Partial<TechniqueFilters>) {
    const params = new URLSearchParams(searchParams.toString());
    for (const [key, val] of Object.entries(next)) {
      if (val) {
        params.set(key, val);
      } else {
        params.delete(key);
      }
    }
    router.push(`?${params.toString()}`);
  }

  const skills = data?.items ?? [];

  return (
    <div className="flex gap-6">
      {/* Taxonomy sidebar */}
      <div className="w-56 shrink-0">
        <h2 className="mb-2 text-sm font-semibold">技能分类</h2>
        <SkillTaxonomy onCategorySelect={updateFilters} />
      </div>

      {/* Main content */}
      <div className="flex-1 space-y-4">
        <h1 className="text-xl font-semibold">技能卡片列表</h1>
        <QueryState
          isLoading={isLoading}
          error={error as Error | null}
          isEmpty={skills.length === 0}
          emptyMessage="暂无匹配技能"
          onRetry={() => refetch()}
        >
          <SkillList skills={skills} onFilterChange={updateFilters} />
        </QueryState>
      </div>
    </div>
  );
}
