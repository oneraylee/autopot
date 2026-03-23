"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { kpiConfigSchema, type KpiConfigFormValues } from "@/schemas/kpi-config";
import { updateKpiConfig } from "@/lib/api/project";

interface KpiConfigFormProps {
  projectId: string;
  defaultValues?: Partial<KpiConfigFormValues>;
}

export function KpiConfigForm({ projectId, defaultValues }: KpiConfigFormProps) {
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<KpiConfigFormValues>({
    resolver: zodResolver(kpiConfigSchema),
    defaultValues: {
      primary_kpi: "",
      threshold: 0,
      weights: { eval: 0, deploy: 0 },
      deploy_constraints: [],
      ...defaultValues,
    },
  });

  const mutation = useMutation({
    mutationFn: (data: KpiConfigFormValues) => updateKpiConfig(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["kpi-config", projectId] });
    },
  });

  return (
    <form onSubmit={handleSubmit((data) => mutation.mutate(data))} className="space-y-4">
      <div>
        <label htmlFor="primary_kpi" className="block text-sm font-medium">
          主要指标
        </label>
        <input
          id="primary_kpi"
          {...register("primary_kpi")}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm"
        />
        {errors.primary_kpi && (
          <p className="mt-1 text-sm text-destructive">{errors.primary_kpi.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="threshold" className="block text-sm font-medium">
          阈值
        </label>
        <input
          id="threshold"
          type="number"
          step="0.01"
          {...register("threshold", { valueAsNumber: true })}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm"
        />
        {errors.threshold && (
          <p className="mt-1 text-sm text-destructive">{errors.threshold.message}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="weights.eval" className="block text-sm font-medium">
            Eval 权重
          </label>
          <input
            id="weights.eval"
            type="number"
            step="0.1"
            {...register("weights.eval", { valueAsNumber: true })}
            className="mt-1 block w-full rounded border px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="weights.deploy" className="block text-sm font-medium">
            Deploy 权重
          </label>
          <input
            id="weights.deploy"
            type="number"
            step="0.1"
            {...register("weights.deploy", { valueAsNumber: true })}
            className="mt-1 block w-full rounded border px-3 py-2 text-sm"
          />
        </div>
      </div>
      {errors.weights && (
        <p className="mt-1 text-sm text-destructive">
          {errors.weights.message ?? "权重之和不能超过 1"}
        </p>
      )}

      <button
        type="submit"
        disabled={mutation.isPending}
        className="rounded bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50"
      >
        {mutation.isPending ? "保存中..." : "保存"}
      </button>

      {mutation.error && (
        <p className="text-sm text-destructive">{mutation.error.message}</p>
      )}
    </form>
  );
}
