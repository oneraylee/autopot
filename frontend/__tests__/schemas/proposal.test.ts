import { describe, it, expect } from "vitest";
import { proposalConfirmSchema } from "@/schemas/proposal";

describe("Proposal Confirm Schema", () => {
  it("test_proposal_confirm_schema_requires_all_fields", () => {
    expect(proposalConfirmSchema.safeParse({}).success).toBe(false);
    expect(proposalConfirmSchema.safeParse({ candidate: {} }).success).toBe(false);
  });

  it("test_proposal_confirm_schema_requires_confirmed_true", () => {
    const invalid = {
      candidate: { name: "A", changes: [] },
      baseline_job_id: "j-1",
      who: "user1",
      when: "2025-01-01",
      confirmed: false,
    };
    expect(proposalConfirmSchema.safeParse(invalid).success).toBe(false);
  });

  it("test_proposal_confirm_schema_accepts_valid", () => {
    const valid = {
      candidate: { name: "A", changes: [] },
      baseline_job_id: "j-1",
      who: "user1",
      when: "2025-01-01",
      confirmed: true,
    };
    expect(proposalConfirmSchema.safeParse(valid).success).toBe(true);
  });
});
