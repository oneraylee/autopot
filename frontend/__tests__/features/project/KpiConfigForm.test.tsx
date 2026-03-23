import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { KpiConfigForm } from "@/features/project/components/KpiConfigForm";

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("KpiConfigForm", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("test_kpi_form_renders_fields", () => {
    render(<KpiConfigForm projectId="p1" />, { wrapper });
    expect(screen.getByLabelText(/主要指标/)).toBeInTheDocument();
    expect(screen.getByLabelText(/阈值/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Eval 权重/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Deploy 权重/)).toBeInTheDocument();
  });

  it("test_kpi_form_validates_weight_sum", async () => {
    const user = userEvent.setup();
    render(<KpiConfigForm projectId="p1" />, { wrapper });
    const evalInput = screen.getByLabelText(/Eval 权重/);
    const deployInput = screen.getByLabelText(/Deploy 权重/);
    await user.clear(evalInput);
    await user.type(evalInput, "0.7");
    await user.clear(deployInput);
    await user.type(deployInput, "0.4");
    await user.click(screen.getByRole("button", { name: /保存/ }));
    await waitFor(() => {
      expect(screen.getByText(/权重之和不能超过/)).toBeInTheDocument();
    });
  });

  it("test_kpi_form_submits_and_refreshes", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          ok: true,
          data: {
            primary_kpi: "漏检率",
            threshold: 0.05,
            weights: { eval: 0.5, deploy: 0.5 },
            deploy_constraints: [],
          },
        }),
      }),
    );
    const user = userEvent.setup();
    render(<KpiConfigForm projectId="p1" />, { wrapper });
    const kpiInput = screen.getByLabelText(/主要指标/);
    const thresholdInput = screen.getByLabelText(/阈值/);
    const evalInput = screen.getByLabelText(/Eval 权重/);
    const deployInput = screen.getByLabelText(/Deploy 权重/);

    await user.clear(kpiInput);
    await user.type(kpiInput, "漏检率");
    await user.clear(thresholdInput);
    await user.type(thresholdInput, "0.05");
    await user.clear(evalInput);
    await user.type(evalInput, "0.5");
    await user.clear(deployInput);
    await user.type(deployInput, "0.5");
    await user.click(screen.getByRole("button", { name: /保存/ }));

    await waitFor(() => {
      expect(vi.mocked(fetch)).toHaveBeenCalled();
    });
  });

  it("test_kpi_page_prefills_existing_values", () => {
    const defaults = {
      primary_kpi: "漏检率",
      threshold: 0.05,
      weights: { eval: 0.6, deploy: 0.4 },
      deploy_constraints: [],
    };
    render(<KpiConfigForm projectId="p1" defaultValues={defaults} />, { wrapper });
    expect(screen.getByLabelText(/主要指标/)).toHaveValue("漏检率");
    expect(screen.getByLabelText(/阈值/)).toHaveValue(0.05);
    expect(screen.getByLabelText(/Eval 权重/)).toHaveValue(0.6);
    expect(screen.getByLabelText(/Deploy 权重/)).toHaveValue(0.4);
  });
});
