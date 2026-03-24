import type { ReactNode } from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import fs from "fs";
import path from "path";

const root = path.resolve(__dirname, "../../..");

describe("Phase7-Step1: Gateway API Client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.resetModules();
  });

  it("test_listProviders_returns_array", async () => {
    const mockProviders = [
      {
        name: "openai",
        models: ["gpt-4o", "gpt-4o-mini"],
        status: "active",
      },
      {
        name: "zhipu",
        models: ["glm-4-flash"],
        status: "active",
      },
    ];
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ok: true, data: mockProviders }),
      }),
    );
    const { listProviders } = await import("@/lib/api/llm-gateway");
    const result = await listProviders();
    expect(Array.isArray(result)).toBe(true);
    expect(result).toHaveLength(2);
    expect(result[0].name).toBe("openai");
    expect(result[0].models).toContain("gpt-4o");
    expect(result[0].status).toBe("active");
  });

  it("test_getUsageReport_supports_params", async () => {
    const mockUsage = {
      items: [
        { date: "2026-03-01", provider: "openai", tokens: 15000, cost: 1.5 },
      ],
      total_tokens: 15000,
      total_cost: 1.5,
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ok: true, data: mockUsage }),
      }),
    );
    const { getUsageReport } = await import("@/lib/api/llm-gateway");
    const result = await getUsageReport({
      start_date: "2026-03-01",
      end_date: "2026-03-31",
      group_by: "provider",
    });
    expect(vi.mocked(fetch)).toHaveBeenCalledWith(
      expect.stringContaining("start_date=2026-03-01"),
      expect.any(Object),
    );
    expect(vi.mocked(fetch)).toHaveBeenCalledWith(
      expect.stringContaining("end_date=2026-03-31"),
      expect.any(Object),
    );
    expect(vi.mocked(fetch)).toHaveBeenCalledWith(
      expect.stringContaining("group_by=provider"),
      expect.any(Object),
    );
    expect(result.items).toHaveLength(1);
    expect(result.total_tokens).toBe(15000);
  });

  it("test_getCallLogs_pagination_and_filter", async () => {
    const mockLogs = {
      items: [
        {
          id: "log-1",
          call_type: "agent_plan",
          provider: "openai",
          model: "gpt-4o",
          input_tokens: 500,
          output_tokens: 200,
          latency_ms: 1200,
          cost: 0.02,
          status: "success",
          created_at: "2026-03-20T10:00:00Z",
        },
      ],
      page: 1,
      page_size: 20,
      total: 1,
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ok: true, data: mockLogs }),
      }),
    );
    const { getCallLogs } = await import("@/lib/api/llm-gateway");
    const result = await getCallLogs({
      page: 1,
      page_size: 20,
      call_type: "agent_plan",
      provider: "openai",
      status: "success",
    });
    expect(vi.mocked(fetch)).toHaveBeenCalledWith(
      expect.stringContaining("page=1"),
      expect.any(Object),
    );
    expect(vi.mocked(fetch)).toHaveBeenCalledWith(
      expect.stringContaining("page_size=20"),
      expect.any(Object),
    );
    expect(vi.mocked(fetch)).toHaveBeenCalledWith(
      expect.stringContaining("call_type=agent_plan"),
      expect.any(Object),
    );
    expect(result.items).toHaveLength(1);
    expect(result.items[0].call_type).toBe("agent_plan");
    expect(result.total).toBe(1);
  });
});

describe("Phase7-Step1: Gateway page file existence", () => {
  it("test_sidebar_settings_entry_visible", () => {
    // Sidebar should have Settings entry
    const sidebarPath = path.join(root, "src/components/Sidebar.tsx");
    const content = fs.readFileSync(sidebarPath, "utf-8");
    expect(content).toContain("Settings");
  });

  it("test_gateway_page_exists", () => {
    expect(
      fs.existsSync(
        path.join(
          root,
          "src/app/(dashboard)/settings/llm-gateway/page.tsx",
        ),
      ),
    ).toBe(true);
  });

  it("test_gateway_hooks_exist", async () => {
    const mod = await import(
      "@/features/settings/hooks/useGateway"
    );
    expect(mod.useProviders).toBeDefined();
    expect(mod.useUsageReport).toBeDefined();
    expect(mod.useCallLogs).toBeDefined();
  });
});

describe("Phase7-Step1: Gateway component rendering", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.resetModules();
  });

  it("test_usage_report_empty_state_renders", async () => {
    vi.doMock("@/features/settings/hooks/useGateway", () => ({
      useProviders: () => ({
        data: [{ name: "openai", models: ["gpt-4o"], status: "active" }],
        isLoading: false,
        error: null,
      }),
      useUsageReport: () => ({
        data: { items: [], total_tokens: 0, total_cost: 0 },
        isLoading: false,
        error: null,
      }),
      useCallLogs: () => ({
        data: { items: [], page: 1, page_size: 20, total: 0 },
        isLoading: false,
        error: null,
      }),
    }));

    const { render, screen } = await import("@testing-library/react");
    const GatewayPage = (await import(
      "@/app/(dashboard)/settings/llm-gateway/page"
    )).default;

    render(<GatewayPage />);

    expect(screen.getByText(/暂无用量数据|暂无报表数据/i)).toBeInTheDocument();
  });

  it("test_call_log_query_cleared_on_unmount", async () => {
    vi.doUnmock("@/features/settings/hooks/useGateway");
    vi.resetModules();

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            ok: true,
            data: {
              items: [],
              page: 1,
              page_size: 20,
              total: 0,
            },
          }),
      }),
    );

    const { renderHook, waitFor } = await import("@testing-library/react");
    const { QueryClient, QueryClientProvider } = await import(
      "@tanstack/react-query"
    );
    const { useCallLogs } = await import("@/features/settings/hooks/useGateway");

    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const removeQueriesSpy = vi.spyOn(queryClient, "removeQueries");

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { unmount } = renderHook(() => useCallLogs({ page: 1, page_size: 20 }), {
      wrapper,
    });

    await waitFor(() => {
      expect(vi.mocked(fetch)).toHaveBeenCalled();
    });

    unmount();

    expect(removeQueriesSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ["llm-gateway", "call-logs"],
      }),
    );
  });

  it("test_provider_list_renders_columns", async () => {
    const { render, screen } = await import("@testing-library/react");
    const { ProviderList } = await import(
      "@/features/settings/components/ProviderList"
    );
    const providers = [
      { name: "openai", models: ["gpt-4o"], status: "active" },
      { name: "zhipu", models: ["glm-4-flash"], status: "inactive" },
    ];
    render(<ProviderList providers={providers} />);
    expect(screen.getByText("openai")).toBeInTheDocument();
    expect(screen.getByText("zhipu")).toBeInTheDocument();
    expect(screen.getByText("gpt-4o")).toBeInTheDocument();
    expect(screen.getByText("glm-4-flash")).toBeInTheDocument();
    expect(screen.getAllByText(/active/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/inactive/i)).toBeInTheDocument();
  });

  it("test_usage_report_date_picker", async () => {
    const { render, screen } = await import("@testing-library/react");
    const { UsageReport } = await import(
      "@/features/settings/components/UsageReport"
    );
    const usageData = {
      items: [
        { date: "2026-03-01", provider: "openai", tokens: 10000, cost: 1.0 },
      ],
      total_tokens: 10000,
      total_cost: 1.0,
    };
    const onParamsChange = vi.fn();
    render(
      <UsageReport
        data={usageData}
        onParamsChange={onParamsChange}
        isLoading={false}
      />,
    );
    // Date inputs should exist
    expect(screen.getByTestId("usage-start-date")).toBeInTheDocument();
    expect(screen.getByTestId("usage-end-date")).toBeInTheDocument();
  });

  it("test_usage_report_group_by_switch", async () => {
    const { render, screen, fireEvent } = await import(
      "@testing-library/react"
    );
    const { UsageReport } = await import(
      "@/features/settings/components/UsageReport"
    );
    const usageData = {
      items: [],
      total_tokens: 0,
      total_cost: 0,
    };
    const onParamsChange = vi.fn();
    render(
      <UsageReport
        data={usageData}
        onParamsChange={onParamsChange}
        isLoading={false}
      />,
    );
    // Group by buttons should exist
    const providerBtn = screen.getByTestId("group-by-provider");
    const callTypeBtn = screen.getByTestId("group-by-call_type");
    const modelBtn = screen.getByTestId("group-by-model");
    expect(providerBtn).toBeInTheDocument();
    expect(callTypeBtn).toBeInTheDocument();
    expect(modelBtn).toBeInTheDocument();

    fireEvent.click(callTypeBtn);
    expect(onParamsChange).toHaveBeenCalledWith(
      expect.objectContaining({ group_by: "call_type" }),
    );
  });

  it("test_usage_report_chart_renders", async () => {
    const { render, screen } = await import("@testing-library/react");
    const { UsageReport } = await import(
      "@/features/settings/components/UsageReport"
    );
    const usageData = {
      items: [
        { date: "2026-03-01", provider: "openai", tokens: 10000, cost: 1.0 },
        { date: "2026-03-02", provider: "openai", tokens: 12000, cost: 1.2 },
      ],
      total_tokens: 22000,
      total_cost: 2.2,
    };
    render(
      <UsageReport
        data={usageData}
        onParamsChange={vi.fn()}
        isLoading={false}
      />,
    );
    expect(screen.getByTestId("usage-chart")).toBeInTheDocument();
  });

  it("test_call_log_table_columns", async () => {
    const { render, screen } = await import("@testing-library/react");
    const { CallLogList } = await import(
      "@/features/settings/components/CallLogList"
    );
    const logs = {
      items: [
        {
          id: "log-1",
          call_type: "agent_plan",
          provider: "openai",
          model: "gpt-4o",
          input_tokens: 500,
          output_tokens: 200,
          latency_ms: 1200,
          cost: 0.02,
          status: "success",
          created_at: "2026-03-20T10:00:00Z",
        },
      ],
      page: 1,
      page_size: 20,
      total: 1,
    };
    render(
      <CallLogList
        data={logs}
        onPageChange={vi.fn()}
        onFilterChange={vi.fn()}
        isLoading={false}
      />,
    );
    // Table headers
    expect(screen.getByText(/call_type|调用类型/i)).toBeInTheDocument();
    expect(screen.getByText(/provider|提供商/i)).toBeInTheDocument();
    expect(screen.getByText(/model|模型/i)).toBeInTheDocument();
    expect(screen.getByText(/tokens/i)).toBeInTheDocument();
    expect(screen.getByText(/latency|延迟/i)).toBeInTheDocument();
    expect(screen.getByText(/cost|费用/i)).toBeInTheDocument();
    expect(screen.getByText(/status|状态/i)).toBeInTheDocument();
    // Row data
    expect(screen.getByText("agent_plan")).toBeInTheDocument();
    expect(screen.getByText("openai")).toBeInTheDocument();
    expect(screen.getByText("gpt-4o")).toBeInTheDocument();
  });

  it("test_call_log_pagination", async () => {
    const { render, screen, fireEvent } = await import(
      "@testing-library/react"
    );
    const { CallLogList } = await import(
      "@/features/settings/components/CallLogList"
    );
    const logs = {
      items: Array.from({ length: 20 }, (_, i) => ({
        id: `log-${i}`,
        call_type: "agent_plan",
        provider: "openai",
        model: "gpt-4o",
        input_tokens: 500,
        output_tokens: 200,
        latency_ms: 1200,
        cost: 0.02,
        status: "success",
        created_at: "2026-03-20T10:00:00Z",
      })),
      page: 1,
      page_size: 20,
      total: 50,
    };
    const onPageChange = vi.fn();
    render(
      <CallLogList
        data={logs}
        onPageChange={onPageChange}
        onFilterChange={vi.fn()}
        isLoading={false}
      />,
    );
    const nextBtn = screen.getByTestId("call-log-next-page");
    expect(nextBtn).toBeInTheDocument();
    fireEvent.click(nextBtn);
    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it("test_call_log_filter_by_call_type", async () => {
    const { render, screen, fireEvent } = await import(
      "@testing-library/react"
    );
    const { CallLogList } = await import(
      "@/features/settings/components/CallLogList"
    );
    const logs = {
      items: [],
      page: 1,
      page_size: 20,
      total: 0,
    };
    const onFilterChange = vi.fn();
    render(
      <CallLogList
        data={logs}
        onPageChange={vi.fn()}
        onFilterChange={onFilterChange}
        isLoading={false}
      />,
    );
    const callTypeFilter = screen.getByTestId("filter-call-type");
    expect(callTypeFilter).toBeInTheDocument();
    fireEvent.change(callTypeFilter, { target: { value: "skill_extract" } });
    expect(onFilterChange).toHaveBeenCalledWith(
      expect.objectContaining({ call_type: "skill_extract" }),
    );
  });

  it("test_call_log_failed_highlight", async () => {
    const { render, screen } = await import("@testing-library/react");
    const { CallLogList } = await import(
      "@/features/settings/components/CallLogList"
    );
    const logs = {
      items: [
        {
          id: "log-fail",
          call_type: "agent_plan",
          provider: "openai",
          model: "gpt-4o",
          input_tokens: 500,
          output_tokens: 0,
          latency_ms: 5000,
          cost: 0,
          status: "failed",
          created_at: "2026-03-20T10:00:00Z",
        },
      ],
      page: 1,
      page_size: 20,
      total: 1,
    };
    render(
      <CallLogList
        data={logs}
        onPageChange={vi.fn()}
        onFilterChange={vi.fn()}
        isLoading={false}
      />,
    );
    const failedRow = screen.getByTestId("call-log-row-log-fail");
    expect(failedRow).toBeInTheDocument();
    expect(failedRow.className).toMatch(/red|error|fail|destructive/i);
  });

  it("test_empty_state_renders", async () => {
    const { render, screen } = await import("@testing-library/react");
    const { ProviderList } = await import(
      "@/features/settings/components/ProviderList"
    );
    render(<ProviderList providers={[]} />);
    expect(screen.getByText(/暂无|no data|empty/i)).toBeInTheDocument();
  });
});
