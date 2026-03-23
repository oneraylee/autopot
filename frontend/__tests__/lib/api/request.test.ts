import { describe, it, expect, vi, beforeEach } from "vitest";

// We test the module exists and has correct types/behavior
describe("Step 3: API 基础客户端与错误处理", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("test_types_file_exists_and_exports", async () => {
    const types = await import("@/lib/api/types");
    expect(types).toBeDefined();
  });

  it("test_errors_file_exports_api_error", async () => {
    const { ApiError } = await import("@/lib/api/errors");
    expect(ApiError).toBeDefined();
    const err = new ApiError("NOT_FOUND", "Not found", "business_error");
    expect(err.code).toBe("NOT_FOUND");
    expect(err.message).toBe("Not found");
    expect(err.type).toBe("business_error");
  });

  it("test_successful_response_unwraps_data", async () => {
    const { request } = await import("@/lib/api/request");
    const mockData = { id: 1, name: "test" };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ok: true, data: mockData }),
      }),
    );
    const result = await request("GET", "/test");
    expect(result).toEqual(mockData);
  });

  it("test_error_response_throws_api_error_with_code_and_message", async () => {
    const { request } = await import("@/lib/api/request");
    const { ApiError } = await import("@/lib/api/errors");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            ok: false,
            error: {
              code: "NOT_FOUND",
              message: "Resource not found",
              details: [],
              type: "business_error",
            },
          }),
      }),
    );
    await expect(request("GET", "/test")).rejects.toThrow(ApiError);
    try {
      await request("GET", "/test");
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      expect((e as InstanceType<typeof ApiError>).code).toBe("NOT_FOUND");
    }
  });

  it("test_network_error_throws_network_error", async () => {
    const { request } = await import("@/lib/api/request");
    const { NetworkError } = await import("@/lib/api/errors");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("Failed to fetch")),
    );
    await expect(request("GET", "/test")).rejects.toThrow(NetworkError);
  });

  it("test_base_url_configurable_via_env", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "http://custom:9000");
    // re-import to pick up env
    vi.resetModules();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ok: true, data: {} }),
      }),
    );
    const { request } = await import("@/lib/api/request");
    await request("GET", "/health");
    expect(vi.mocked(fetch)).toHaveBeenCalledWith(
      "http://custom:9000/health",
      expect.any(Object),
    );
  });

  it("test_request_includes_json_content_type", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ok: true, data: {} }),
      }),
    );
    const { request } = await import("@/lib/api/request");
    await request("POST", "/test", { body: { foo: "bar" } });
    expect(vi.mocked(fetch)).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          "Content-Type": "application/json",
        }),
      }),
    );
  });
});
