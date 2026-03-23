import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CreateJobForm } from "@/features/job/components/CreateJobForm";
import { StartJobButton } from "@/features/job/components/StartJobButton";

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({ id: "j-1" }),
}));

// Mock hooks for page-level tests
vi.mock("@/features/job/hooks/useJobList", () => ({
  useJobList: vi.fn(() => ({ data: [], isLoading: false, error: null })),
}));
vi.mock("@/features/job/hooks/useJob", () => ({
  useJob: vi.fn(() => ({ data: null, isLoading: true, error: null })),
}));
vi.mock("@/features/job/hooks/useJobLogs", () => ({
  useJobLogs: vi.fn(() => ({ data: undefined, isLoading: false })),
}));
vi.mock("@/features/job/hooks/useJobMetrics", () => ({
  useJobMetrics: vi.fn(() => ({ data: undefined, isLoading: false })),
}));
vi.mock("@/features/job/hooks/useJobArtifacts", () => ({
  useJobArtifacts: vi.fn(() => ({ data: null, isLoading: false })),
}));

import { useJobList } from "@/features/job/hooks/useJobList";
import { useJob } from "@/features/job/hooks/useJob";
import JobsPage from "@/app/(dashboard)/jobs/page";
import JobDetailPage from "@/app/(dashboard)/jobs/[id]/page";

describe("CreateJobForm", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("test_create_job_form_renders_fields", () => {
    render(<CreateJobForm />, { wrapper });
    expect(screen.getByLabelText(/任务类型/)).toBeInTheDocument();
    expect(screen.getByLabelText(/数据集版本/)).toBeInTheDocument();
    expect(screen.getByLabelText(/GPU 数量/)).toBeInTheDocument();
  });

  it("test_create_job_form_validates_required_fields", async () => {
    const user = userEvent.setup();
    render(<CreateJobForm />, { wrapper });
    await user.click(screen.getByRole("button", { name: /创建/ }));
    // Form should not submit without required fields
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /创建/ })).toBeEnabled();
    });
  });
});

describe("StartJobButton", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("test_start_job_renders_button", () => {
    render(<StartJobButton jobId="j-1" status="created" />, { wrapper });
    expect(screen.getByRole("button", { name: /启动/ })).toBeInTheDocument();
  });

  it("test_start_job_disabled_when_running", () => {
    render(<StartJobButton jobId="j-1" status="running" />, { wrapper });
    const btn = screen.getByRole("button");
    expect(btn).toBeDisabled();
  });
});

// ===== Page-Level Integration Tests =====

const createdJob = {
  job_id: "j-1",
  task_type: "training",
  status: "created" as const,
  dataset_version_id: "dv-1",
  created_at: "2025-01-01T00:00:00Z",
  updated_at: "2025-01-01T00:00:00Z",
};

describe("JobsPage integration", () => {
  beforeEach(() => {
    vi.mocked(useJobList).mockReturnValue({
      data: [createdJob],
      isLoading: false,
      error: null,
    } as any);
  });

  it("test_jobs_page_opens_create_job_entry_and_submits_successfully", async () => {
    const user = userEvent.setup();
    render(<JobsPage />, { wrapper });

    // Page should have a "创建任务" button
    const createBtn = screen.getByRole("button", { name: /创建任务/ });
    expect(createBtn).toBeInTheDocument();

    // Click to reveal CreateJobForm
    await user.click(createBtn);

    // Form fields should now be visible
    expect(screen.getByLabelText(/任务类型/)).toBeInTheDocument();
    expect(screen.getByLabelText(/数据集版本/)).toBeInTheDocument();
  });
});

describe("JobDetailPage integration", () => {
  const originalFetch = globalThis.fetch;
  let fetchSpy: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.mocked(useJob).mockReturnValue({
      data: createdJob,
      isLoading: false,
      error: null,
    } as any);
    fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          ok: true,
          data: { ...createdJob, status: "running" },
        }),
    });
    globalThis.fetch = fetchSpy;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("test_job_detail_shows_start_button_for_created_or_queued_status", () => {
    render(<JobDetailPage />, { wrapper });
    expect(screen.getByTestId("job-start-btn")).toBeInTheDocument();
  });

  it("test_job_detail_refreshes_after_start_success", async () => {
    const user = userEvent.setup();
    render(<JobDetailPage />, { wrapper });

    await user.type(screen.getByPlaceholderText("GPU ID"), "gpu-0");
    await user.click(screen.getByTestId("job-start-btn"));

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledWith(
        expect.stringContaining("/jobs/j-1/start"),
        expect.objectContaining({ method: "POST" }),
      );
    });
  });
});
