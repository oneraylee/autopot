"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { createJobSchema, type CreateJobFormValues } from "@/schemas/job";
import { createJob } from "@/lib/api/job";

export function CreateJobForm() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CreateJobFormValues>({
    resolver: zodResolver(createJobSchema),
    defaultValues: {
      task_type: "",
      dataset_version_id: "",
      config: {},
      resources: { gpu_count: 1 },
    },
  });

  const mutation = useMutation({
    mutationFn: createJob,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      router.push(`/jobs/${data.job_id}`);
    },
  });

  return (
    <form onSubmit={handleSubmit((data) => mutation.mutate(data))} className="space-y-4">
      <div>
        <label htmlFor="task_type" className="block text-sm font-medium">
          任务类型
        </label>
        <select
          id="task_type"
          {...register("task_type")}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm"
        >
          <option value="">请选择</option>
          <option value="training">training</option>
          <option value="evaluation">evaluation</option>
        </select>
        {errors.task_type && (
          <p className="mt-1 text-sm text-destructive">{errors.task_type.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="dataset_version_id" className="block text-sm font-medium">
          数据集版本
        </label>
        <input
          id="dataset_version_id"
          {...register("dataset_version_id")}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm"
        />
        {errors.dataset_version_id && (
          <p className="mt-1 text-sm text-destructive">{errors.dataset_version_id.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="resources.gpu_count" className="block text-sm font-medium">
          GPU 数量
        </label>
        <input
          id="resources.gpu_count"
          type="number"
          min={1}
          {...register("resources.gpu_count", { valueAsNumber: true })}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm"
        />
        {errors.resources?.gpu_count && (
          <p className="mt-1 text-sm text-destructive">{errors.resources.gpu_count.message}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={mutation.isPending}
        className="rounded bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50"
        data-testid="job-create-btn"
      >
        {mutation.isPending ? "创建中..." : "创建"}
      </button>

      {mutation.error && (
        <p className="text-sm text-destructive">{mutation.error.message}</p>
      )}
    </form>
  );
}
