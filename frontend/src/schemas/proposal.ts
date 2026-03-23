import { z } from "zod";

export const proposalValidateSchema = z.object({
  job_id: z.string().min(1),
  run_id: z.string().min(1),
});

export type ProposalValidateFormValues = z.infer<typeof proposalValidateSchema>;

export const proposalConfirmSchema = z.object({
  candidate: z.object({
    name: z.string().min(1),
    changes: z.array(z.unknown()),
  }),
  baseline_job_id: z.string().min(1),
  who: z.string().min(1),
  when: z.string().min(1),
  confirmed: z.literal(true),
  idempotency_key: z.string().optional(),
});

export type ProposalConfirmFormValues = z.infer<typeof proposalConfirmSchema>;
