import { z } from "zod";

export const kpiConfigSchema = z
  .object({
    primary_kpi: z.string().min(1),
    threshold: z.number().min(0).max(1),
    weights: z.object({
      eval: z.number().min(0).max(1),
      deploy: z.number().min(0).max(1),
    }),
    deploy_constraints: z.array(
      z.object({
        metric: z.string().min(1),
        operator: z.string().min(1),
        value: z.number(),
      }),
    ),
  })
  .refine((d) => d.weights.eval + d.weights.deploy <= 1, {
    message: "eval + deploy 权重之和不能超过 1",
    path: ["weights"],
  });

export type KpiConfigFormValues = z.infer<typeof kpiConfigSchema>;
