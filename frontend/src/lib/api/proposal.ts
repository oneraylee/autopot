import { request } from "./request";

export interface ValidateResult {
  accepted: number;
  rejected: number;
  details: Array<{ name: string; status: string; reason?: string }>;
}

export interface ProposalConfirmPayload {
  candidate: { name: string; changes: unknown[] };
  baseline_job_id: string;
  who: string;
  when: string;
  confirmed: true;
  idempotency_key?: string;
}

export interface ProposalConfirmResult {
  job_id: string;
}

export function validateProposals(
  jobId: string,
  runId: string,
): Promise<ValidateResult> {
  return request<ValidateResult>("POST", "/proposals/validate", {
    body: { job_id: jobId, run_id: runId },
  });
}

export function createFromProposal(
  payload: ProposalConfirmPayload,
): Promise<ProposalConfirmResult> {
  return request<ProposalConfirmResult>(
    "POST",
    "/proposals/create-from-candidate",
    { body: payload },
  );
}
