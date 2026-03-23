import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { DeployBenchmarkView } from "@/features/export/components/DeployBenchmark";
import * as exportApi from "@/lib/api/export";

vi.mock("@/lib/api/export");

function createWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

describe("DeployBenchmark", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("test_deploy_benchmark_renders_metrics_table", async () => {
    vi.mocked(exportApi.getDeployBenchmark).mockResolvedValue({
      latency_ms: 19.5,
      throughput_fps: 120,
      memory_mb: 2048,
    });
    render(<DeployBenchmarkView exportId="e1" />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(screen.getByText("19.5")).toBeInTheDocument();
    });
    expect(screen.getByText("120")).toBeInTheDocument();
    expect(screen.getByText("2048")).toBeInTheDocument();
  });

  it("test_deploy_benchmark_empty_state", async () => {
    vi.mocked(exportApi.getDeployBenchmark).mockRejectedValue(new Error("NOT_FOUND"));
    render(<DeployBenchmarkView exportId="e1" />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(screen.getByText(/暂无基准数据|错误/)).toBeInTheDocument();
    });
  });

  it("test_deploy_benchmark_component_renders_after_export_ready", async () => {
    vi.mocked(exportApi.getDeployBenchmark).mockResolvedValue({
      latency_ms: 22.3,
      throughput_fps: 95,
      memory_mb: 3072,
    });
    render(<DeployBenchmarkView exportId="e-ready" />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(screen.getByText("22.3")).toBeInTheDocument();
    });
    expect(screen.getByText("95")).toBeInTheDocument();
    expect(screen.getByText("3072")).toBeInTheDocument();
    expect(screen.getByText("部署基准")).toBeInTheDocument();
  });
});
