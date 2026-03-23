"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useMutationWithToast } from "@/lib/query/useMutationWithToast";
import { createExportSchema, type CreateExportFormValues } from "@/schemas/export";
import { createExport } from "@/lib/api/export";

interface CreateExportFormProps {
  onSuccess?: (exportId: string) => void;
}

export function CreateExportForm({ onSuccess: onSuccessCallback }: CreateExportFormProps = {}) {
  const router = useRouter();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CreateExportFormValues>({
    resolver: zodResolver(createExportSchema),
    defaultValues: { job_id: "", run_id: "", backend: "tensorrt" },
  });

  const mutation = useMutationWithToast({
    mutationFn: createExport,
    successMessage: "导出任务已创建",
    onSuccess: (data) => {
      onSuccessCallback?.(data.export_id);
      router.push("/exports");
    },
  });

  return (
    <form onSubmit={handleSubmit((data) => mutation.mutate(data))} className="space-y-4">
      <div>
        <label htmlFor="export-job-id" className="block text-sm font-medium">
          Job ID
        </label>
        <input
          id="export-job-id"
          {...register("job_id")}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm"
        />
        {errors.job_id && (
          <p className="mt-1 text-sm text-destructive">{errors.job_id.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="export-run-id" className="block text-sm font-medium">
          Run ID
        </label>
        <input
          id="export-run-id"
          {...register("run_id")}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm"
        />
        {errors.run_id && (
          <p className="mt-1 text-sm text-destructive">{errors.run_id.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="export-backend" className="block text-sm font-medium">
          Backend
        </label>
        <select
          id="export-backend"
          {...register("backend")}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm"
        >
          <option value="tensorrt">tensorrt</option>
        </select>
      </div>

      <button
        type="submit"
        disabled={mutation.isPending}
        className="rounded bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50"
        data-testid="export-create-btn"
      >
        {mutation.isPending ? "创建中..." : "创建导出"}
      </button>

      {mutation.error && (
        <p className="text-sm text-destructive">{mutation.error.message}</p>
      )}
    </form>
  );
}
