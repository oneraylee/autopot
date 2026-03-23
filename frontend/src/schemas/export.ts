import { z } from "zod";

export const createExportSchema = z.object({
  job_id: z.string().min(1),
  run_id: z.string().min(1),
  backend: z.enum(["tensorrt"]),
});

export type CreateExportFormValues = z.infer<typeof createExportSchema>;
