"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  createSourceSchema,
  type CreateSourceFormValues,
} from "@/schemas/knowledge";
import { knowledgeApi } from "@/lib/api/knowledge";

interface CreateSourceFormProps {
  onSuccess?: () => void;
}

export function CreateSourceForm({ onSuccess }: CreateSourceFormProps) {
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<CreateSourceFormValues>({
    resolver: zodResolver(createSourceSchema),
    defaultValues: { source_type: "local", trust_level: 3 },
  });

  const mutation = useMutation({
    mutationFn: knowledgeApi.createSource,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledge", "sources"] });
      reset();
      onSuccess?.();
    },
  });

  return (
    <form
      onSubmit={handleSubmit((data) => mutation.mutate(data))}
      className="space-y-4"
    >
      <div>
        <label htmlFor="name" className="block text-sm font-medium">
          来源名称
        </label>
        <input
          id="name"
          {...register("name")}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm"
        />
        {errors.name && (
          <p className="mt-1 text-sm text-destructive" data-testid="source-form-error">
            {errors.name.message ?? "必填"}
          </p>
        )}
      </div>

      <div>
        <label htmlFor="source_type" className="block text-sm font-medium">
          来源类型
        </label>
        <select
          id="source_type"
          {...register("source_type")}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm"
        >
          <option value="local">local</option>
          <option value="web">web</option>
          <option value="official_doc">official_doc</option>
          <option value="internal_experiment">internal_experiment</option>
        </select>
        {errors.source_type && (
          <p className="mt-1 text-sm text-destructive">
            {errors.source_type.message ?? "必填"}
          </p>
        )}
      </div>

      <div>
        <label htmlFor="uri" className="block text-sm font-medium">
          URI / 路径
        </label>
        <input
          id="uri"
          {...register("uri")}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm"
        />
        {errors.uri && (
          <p className="mt-1 text-sm text-destructive" data-testid="source-form-error">
            {errors.uri.message ?? "必填"}
          </p>
        )}
      </div>

      <div>
        <label htmlFor="trust_level" className="block text-sm font-medium">
          信任等级（1-5）
        </label>
        <input
          id="trust_level"
          type="number"
          min={1}
          max={5}
          {...register("trust_level", { valueAsNumber: true })}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm"
        />
        {errors.trust_level && (
          <p className="mt-1 text-sm text-destructive">
            {errors.trust_level.message ?? "必填"}
          </p>
        )}
      </div>

      <button
        type="submit"
        disabled={mutation.isPending}
        className="rounded bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50"
        data-testid="create-source-btn"
      >
        {mutation.isPending ? "注册中..." : "注册来源"}
      </button>

      {mutation.error && (
        <p className="text-sm text-destructive">{mutation.error.message}</p>
      )}
    </form>
  );
}
