import { z } from "zod";

export const createJobSchema = z.object({
  task_type: z.string().min(1),
  dataset_version_id: z.string().min(1),
  config: z.record(z.unknown()).default({}),
  resources: z.object({
    gpu_count: z.number().int().positive(),
  }),
});

export type CreateJobFormValues = z.infer<typeof createJobSchema>;

export const startJobSchema = z.object({
  gpu_id: z.string().min(1),
});

export type StartJobFormValues = z.infer<typeof startJobSchema>;
