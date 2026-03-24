"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  createTechniqueSchema,
  type CreateTechniqueFormValues,
} from "@/schemas/knowledge";
import { knowledgeApi } from "@/lib/api/knowledge";

interface SkillEditFormProps {
  techniqueId?: string;
  defaultValues?: Partial<CreateTechniqueFormValues>;
  onSuccess?: () => void;
}

export function SkillEditForm({
  techniqueId,
  defaultValues,
  onSuccess,
}: SkillEditFormProps) {
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CreateTechniqueFormValues>({
    resolver: zodResolver(createTechniqueSchema),
    defaultValues: {
      category: "training",
      task_type: "det",
      ...defaultValues,
    },
  });

  const mutation = useMutation({
    mutationFn: (data: CreateTechniqueFormValues) =>
      techniqueId
        ? knowledgeApi.updateTechnique(techniqueId, data)
        : knowledgeApi.createTechnique(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledge", "techniques"] });
      onSuccess?.();
    },
  });

  return (
    <form
      onSubmit={handleSubmit((data) => mutation.mutate(data))}
      className="space-y-4"
    >
      <div>
        <label htmlFor="skill_code" className="block text-sm font-medium">
          技能编码 (skill_code)
        </label>
        <input
          id="skill_code"
          {...register("skill_code")}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm font-mono"
          placeholder="train.augment.mosaic"
        />
        {errors.skill_code && (
          <p className="mt-1 text-sm text-destructive">
            {errors.skill_code.message}
          </p>
        )}
      </div>

      <div>
        <label htmlFor="name_field" className="block text-sm font-medium">
          技能名称
        </label>
        <input
          id="name_field"
          {...register("name")}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm"
        />
        {errors.name && (
          <p className="mt-1 text-sm text-destructive">{errors.name.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="category_field" className="block text-sm font-medium">
          分类 (category)
        </label>
        <select
          id="category_field"
          {...register("category")}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm"
        >
          <option value="training">training</option>
          <option value="model">model</option>
          <option value="data">data</option>
          <option value="eval_deploy">eval_deploy</option>
        </select>
      </div>

      <div>
        <label htmlFor="layer_field" className="block text-sm font-medium">
          层级 (layer)
        </label>
        <input
          id="layer_field"
          {...register("layer")}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm"
        />
        {errors.layer && (
          <p className="mt-1 text-sm text-destructive">{errors.layer.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="task_type_field" className="block text-sm font-medium">
          任务类型 (task_type)
        </label>
        <select
          id="task_type_field"
          {...register("task_type")}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm"
        >
          <option value="det">det</option>
          <option value="seg">seg</option>
          <option value="cls">cls</option>
          <option value="multi">multi</option>
        </select>
      </div>

      <div>
        <label htmlFor="summary_field" className="block text-sm font-medium">
          摘要（可选）
        </label>
        <textarea
          id="summary_field"
          {...register("summary")}
          rows={2}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm"
        />
      </div>

      <button
        type="submit"
        disabled={mutation.isPending}
        className="rounded bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50"
      >
        {mutation.isPending ? "保存中..." : techniqueId ? "更新技能" : "创建技能"}
      </button>

      {mutation.error && (
        <p className="text-sm text-destructive">
          {(mutation.error as Error).message}
        </p>
      )}
    </form>
  );
}
