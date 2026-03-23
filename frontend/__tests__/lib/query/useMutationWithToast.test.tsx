import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useMutationWithToast } from "@/lib/query/useMutationWithToast";
import type { ReactNode } from "react";

function createWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

describe("useMutationWithToast", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("test_mutation_success_calls_onSuccess", async () => {
    let successCalled = false;
    const { result } = renderHook(
      () =>
        useMutationWithToast({
          mutationFn: async (val: string) => val.toUpperCase(),
          successMessage: "操作成功",
          onSuccess: () => {
            successCalled = true;
          },
        }),
      { wrapper: createWrapper() },
    );

    result.current.mutate("hello");
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(successCalled).toBe(true);
  });

  it("test_mutation_failure_sets_error", async () => {
    const { result } = renderHook(
      () =>
        useMutationWithToast({
          mutationFn: async () => {
            throw new Error("fail");
          },
          successMessage: "ok",
        }),
      { wrapper: createWrapper() },
    );

    result.current.mutate(undefined);
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe("fail");
  });

  it("test_mutation_loading_returns_is_pending", async () => {
    let resolve: (v: string) => void;
    const promise = new Promise<string>((r) => {
      resolve = r;
    });

    const { result } = renderHook(
      () =>
        useMutationWithToast({
          mutationFn: () => promise,
          successMessage: "ok",
        }),
      { wrapper: createWrapper() },
    );

    result.current.mutate(undefined);
    await waitFor(() => expect(result.current.isPending).toBe(true));
    resolve!("done");
    await waitFor(() => expect(result.current.isPending).toBe(false));
  });
});
