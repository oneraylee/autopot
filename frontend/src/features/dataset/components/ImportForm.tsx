"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { datasetImportSchema, type DatasetImportFormValues } from "@/schemas/dataset";
import { importDatasetVersion } from "@/lib/api/dataset";

interface ImportFormProps {
  datasetId: string;
}

export function ImportForm({ datasetId }: ImportFormProps) {
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<DatasetImportFormValues>({
    resolver: zodResolver(datasetImportSchema),
    defaultValues: { version: 1, manifest_uri: "" },
  });

  const mutation = useMutation({
    mutationFn: (data: DatasetImportFormValues) =>
      importDatasetVersion(datasetId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
      reset();
    },
  });

  return (
    <form onSubmit={handleSubmit((data) => mutation.mutate(data))} className="space-y-4">
      <div>
        <label htmlFor="version" className="block text-sm font-medium">
          版本号
        </label>
        <input
          id="version"
          type="number"
          {...register("version", { valueAsNumber: true })}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm"
        />
        {errors.version && (
          <p className="mt-1 text-sm text-destructive">
            {errors.version.message ?? "必须为正整数"}
          </p>
        )}
      </div>

      <div>
        <label htmlFor="manifest_uri" className="block text-sm font-medium">
          Manifest URI
        </label>
        <input
          id="manifest_uri"
          {...register("manifest_uri")}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm"
        />
        {errors.manifest_uri && (
          <p className="mt-1 text-sm text-destructive">{errors.manifest_uri.message}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={mutation.isPending}
        className="rounded bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50"
        data-testid="dataset-import-btn"
      >
        {mutation.isPending ? "导入中..." : "导入"}
      </button>

      {mutation.error && (
        <p className="text-sm text-destructive">{mutation.error.message}</p>
      )}
    </form>
  );
}
