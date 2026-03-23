import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CreateExportForm } from "@/features/export/components/CreateExportForm";

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

describe("CreateExportForm", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("test_export_form_renders_fields", () => {
    render(<CreateExportForm />, { wrapper });
    expect(screen.getByLabelText(/Job ID/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Run ID/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Backend/)).toBeInTheDocument();
  });

  it("test_export_form_backend_shows_tensorrt", () => {
    render(<CreateExportForm />, { wrapper });
    const select = screen.getByLabelText(/Backend/);
    expect(select).toBeInTheDocument();
    expect(screen.getByText("tensorrt")).toBeInTheDocument();
  });
});
