import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(
      QueryClientProvider,
      { client: queryClient },
      children,
    );
  };
}

describe("Step 4: TanStack Query 集成与健康检查", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.resetModules();
  });

  it("test_providers_file_exists", async () => {
    const mod = await import("@/app/providers");
    expect(mod.Providers).toBeDefined();
  });

  it("test_health_check_returns_connected_when_backend_up", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ok: true, data: { status: "ok" } }),
      }),
    );
    const { useHealthCheck } = await import("@/lib/query/useHealthCheck");
    const { result } = renderHook(() => useHealthCheck(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.isConnected).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it("test_health_check_returns_error_when_backend_down", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("Failed to fetch")),
    );
    const { useHealthCheck } = await import("@/lib/query/useHealthCheck");
    const { result } = renderHook(() => useHealthCheck(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.isConnected).toBe(false);
    expect(result.current.error).not.toBeNull();
  });
});
