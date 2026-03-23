import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { ExportStatus } from "@/features/export/components/ExportStatus";
import * as exportApi from "@/lib/api/export";
import ExportsPage from "@/app/(dashboard)/exports/page";

vi.mock("@/lib/api/export");
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

function createWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

describe("ExportStatus", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("test_export_status_renders_status", async () => {
    vi.mocked(exportApi.getExportStatus).mockResolvedValue({
      export_id: "e1",
      job_id: "j1",
      run_id: "r1",
      backend: "tensorrt",
      status: "succeeded",
      created_at: "2024-01-01T00:00:00Z",
    });
    render(<ExportStatus exportId="e1" />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(screen.getByText("succeeded")).toBeInTheDocument();
    });
  });

  it("test_export_status_shows_error_on_failure", async () => {
    vi.mocked(exportApi.getExportStatus).mockResolvedValue({
      export_id: "e1",
      job_id: "j1",
      run_id: "r1",
      backend: "tensorrt",
      status: "failed",
      created_at: "2024-01-01T00:00:00Z",
    });
    render(<ExportStatus exportId="e1" />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(screen.getByText("failed")).toBeInTheDocument();
    });
  });

  it("test_export_status_shows_loading", () => {
    vi.mocked(exportApi.getExportStatus).mockReturnValue(new Promise(() => {})); // never resolves
    render(<ExportStatus exportId="e1" />, { wrapper: createWrapper() });
    expect(screen.getByText(/加载中/)).toBeInTheDocument();
  });
});

describe("ExportsPage integration", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("test_export_page_stores_export_id_after_create_success", async () => {
    const user = userEvent.setup();

    const exportTask: exportApi.ExportTask = {
      export_id: "e-new",
      job_id: "j-1",
      run_id: "r-1",
      backend: "tensorrt",
      status: "queued",
      created_at: "2024-01-01T00:00:00Z",
    };
    vi.mocked(exportApi.createExport).mockResolvedValue(exportTask);
    vi.mocked(exportApi.getExportStatus).mockResolvedValue(exportTask);

    render(<ExportsPage />, { wrapper: createWrapper() });

    // Fill in form fields
    await user.type(screen.getByLabelText(/Job ID/), "j-1");
    await user.type(screen.getByLabelText(/Run ID/), "r-1");
    await user.click(screen.getByTestId("export-create-btn"));

    // After success, ExportStatus should appear with the export_id
    await waitFor(() => {
      expect(screen.getByText("e-new")).toBeInTheDocument();
    });
  });

  it("test_export_status_component_renders_after_create", async () => {
    const user = userEvent.setup();

    const createResponse: exportApi.ExportTask = {
      export_id: "e-777",
      job_id: "j-1",
      run_id: "r-1",
      backend: "tensorrt",
      status: "running",
      created_at: "2024-01-01T00:00:00Z",
    };

    vi.mocked(exportApi.createExport).mockResolvedValue(createResponse);
    vi.mocked(exportApi.getExportStatus).mockResolvedValue(createResponse);

    render(<ExportsPage />, { wrapper: createWrapper() });

    await user.type(screen.getByLabelText(/Job ID/), "j-1");
    await user.type(screen.getByLabelText(/Run ID/), "r-1");
    await user.click(screen.getByTestId("export-create-btn"));

    // ExportStatus should render showing "running"
    await waitFor(() => {
      expect(screen.getByText("running")).toBeInTheDocument();
    });
  });
});

describe("Export polling", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("test_export_polling_stops_on_terminal_status", async () => {
    let callCount = 0;
    vi.mocked(exportApi.getExportStatus).mockImplementation(() => {
      callCount++;
      return Promise.resolve({
        export_id: "e1",
        job_id: "j1",
        run_id: "r1",
        backend: "tensorrt",
        status: "succeeded",
        created_at: "2024-01-01T00:00:00Z",
      });
    });

    const qc = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const Wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    );

    render(<ExportStatus exportId="e1" />, { wrapper: Wrapper });

    await waitFor(() => {
      expect(screen.getByText("succeeded")).toBeInTheDocument();
    });

    // Record calls so far, then wait and check no more calls
    const callsAfterRender = callCount;

    // Wait real time to verify no further polling
    await new Promise((r) => setTimeout(r, 200));

    // Polling should have stopped on terminal status — no significant extra calls
    expect(callCount).toBeLessThanOrEqual(callsAfterRender + 1);
  });
});
