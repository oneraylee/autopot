import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ValidateForm } from "@/features/proposal/components/ValidateForm";
import { ConfirmCreateDialog } from "@/features/proposal/components/ConfirmCreateDialog";
import { NextExperiments } from "@/features/job/components/NextExperiments";
import type { Candidate } from "@/lib/api/analysis";

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

describe("ValidateForm", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("test_validate_form_renders", () => {
    render(<ValidateForm />, { wrapper });
    expect(screen.getByLabelText(/Job ID/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Run ID/)).toBeInTheDocument();
  });
});

describe("ConfirmCreateDialog", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("test_confirm_dialog_renders_candidate_info", () => {
    const candidate = { name: "A", changes: [{ field: "lr", from: "0.01", to: "0.001" }] };
    render(
      <ConfirmCreateDialog
        open={true}
        onClose={() => {}}
        candidate={candidate}
        baselineJobId="j-1"
      />,
      { wrapper },
    );
    expect(screen.getByText(/候选方案/)).toBeInTheDocument();
    expect(screen.getByText("A")).toBeInTheDocument();
  });

  it("test_confirm_dialog_requires_who_and_when", () => {
    const candidate = { name: "A", changes: [] };
    render(
      <ConfirmCreateDialog
        open={true}
        onClose={() => {}}
        candidate={candidate}
        baselineJobId="j-1"
      />,
      { wrapper },
    );
    expect(screen.getByLabelText(/操作人/)).toBeInTheDocument();
    expect(screen.getByLabelText(/日期/)).toBeInTheDocument();
  });
});

// ===== Step 3 Integration Tests =====

describe("Candidate → ConfirmCreateDialog flow", () => {
  const originalFetch = globalThis.fetch;
  beforeEach(() => {
    vi.restoreAllMocks();
    pushMock.mockClear();
  });
  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  const candidate: Candidate = {
    name: "Candidate A",
    changes: { lr: 0.001 },
    expected: { kpi_delta: { business_kpi: -0.02 } },
    evidence_refs: ["ref1"],
  };

  it("test_candidate_create_button_opens_confirm_dialog", async () => {
    const user = userEvent.setup();
    const onCreateTask = vi.fn();
    render(
      <NextExperiments
        baselineJobId="j-1"
        candidates={[candidate]}
        onCreateTask={onCreateTask}
      />,
    );

    const createBtn = screen.getByTestId("candidate-create-task-btn");
    await user.click(createBtn);
    expect(onCreateTask).toHaveBeenCalledWith(candidate);
  });

  it("test_confirm_dialog_submits_and_redirects_to_new_job", async () => {
    const user = userEvent.setup();
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ ok: true, data: { job_id: "j-new" } }),
    });

    render(
      <ConfirmCreateDialog
        open={true}
        onClose={() => {}}
        candidate={{ name: "A", changes: [] }}
        baselineJobId="j-1"
      />,
      { wrapper },
    );

    await user.type(screen.getByLabelText(/操作人/), "tester");
    await user.click(screen.getByTestId("candidate-create-btn"));

    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith("/jobs/j-new");
    });
  });
});
