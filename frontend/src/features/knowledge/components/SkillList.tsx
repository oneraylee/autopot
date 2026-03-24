"use client";

import type { TechniqueSummary, TechniqueFilters } from "@/features/knowledge/types";

interface SkillListProps {
  skills: TechniqueSummary[];
  onFilterChange?: (filters: Partial<TechniqueFilters>) => void;
}

export function SkillList({ skills, onFilterChange }: SkillListProps) {
  function handleSelectChange(
    field: keyof TechniqueFilters,
    value: string,
  ) {
    onFilterChange?.({ [field]: value || undefined } as Partial<TechniqueFilters>);
  }

  return (
    <div className="space-y-4" data-testid="skill-list">
      {/* 四维筛选器 */}
      <div className="flex flex-wrap gap-3">
        <div>
          <label htmlFor="filter-category" className="block text-xs text-muted-foreground">
            分类 (category)
          </label>
          <select
            id="filter-category"
            className="rounded border px-2 py-1 text-sm"
            onChange={(e) => handleSelectChange("category", e.target.value)}
          >
            <option value="">全部</option>
            <option value="training">training</option>
            <option value="model">model</option>
            <option value="data">data</option>
            <option value="eval_deploy">eval_deploy</option>
          </select>
        </div>

        <div>
          <label htmlFor="filter-layer" className="block text-xs text-muted-foreground">
            层级 (layer)
          </label>
          <select
            id="filter-layer"
            className="rounded border px-2 py-1 text-sm"
            onChange={(e) => handleSelectChange("layer", e.target.value)}
          >
            <option value="">全部</option>
            <option value="optimizer">optimizer</option>
            <option value="schedule">schedule</option>
            <option value="augment">augment</option>
            <option value="backbone">backbone</option>
            <option value="neck">neck</option>
            <option value="head">head</option>
            <option value="attention">attention</option>
          </select>
        </div>

        <div>
          <label htmlFor="filter-task_type" className="block text-xs text-muted-foreground">
            任务类型 (task_type)
          </label>
          <select
            id="filter-task_type"
            className="rounded border px-2 py-1 text-sm"
            onChange={(e) => handleSelectChange("task_type", e.target.value)}
          >
            <option value="">全部</option>
            <option value="det">det</option>
            <option value="seg">seg</option>
            <option value="cls">cls</option>
            <option value="multi">multi</option>
          </select>
        </div>

        <div>
          <label htmlFor="filter-maturity" className="block text-xs text-muted-foreground">
            成熟度 (maturity)
          </label>
          <select
            id="filter-maturity"
            className="rounded border px-2 py-1 text-sm"
            onChange={(e) => handleSelectChange("maturity", e.target.value)}
          >
            <option value="">全部</option>
            <option value="draft">draft</option>
            <option value="reviewed">reviewed</option>
            <option value="verified">verified</option>
            <option value="deprecated">deprecated</option>
          </select>
        </div>
      </div>

      {/* 技能列表 */}
      {skills.length === 0 ? (
        <div className="p-6 text-muted-foreground">暂无匹配技能</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-muted-foreground">
                <th className="px-4 py-2">技能编码</th>
                <th className="px-4 py-2">名称</th>
                <th className="px-4 py-2">分类</th>
                <th className="px-4 py-2">层级</th>
                <th className="px-4 py-2">任务类型</th>
                <th className="px-4 py-2">成熟度</th>
                <th className="px-4 py-2">状态</th>
              </tr>
            </thead>
            <tbody>
              {skills.map((s) => (
                <tr
                  key={s.technique_id}
                  data-testid={`skill-row-${s.technique_id}`}
                  className="border-b hover:bg-accent/50"
                >
                  <td className="px-4 py-2 font-mono text-xs">{s.skill_code}</td>
                  <td className="px-4 py-2 font-medium">{s.name}</td>
                  <td className="px-4 py-2">{s.category}</td>
                  <td className="px-4 py-2">{s.layer}</td>
                  <td className="px-4 py-2">{s.task_type}</td>
                  <td className="px-4 py-2">{s.maturity}</td>
                  <td className="px-4 py-2">{s.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
