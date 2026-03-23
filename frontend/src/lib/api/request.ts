import type { ApiResponse } from "./types";
import { ApiError, NetworkError } from "./errors";

function getBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
}

export interface RequestOptions {
  body?: unknown;
  params?: Record<string, string>;
}

export async function request<T = unknown>(
  method: string,
  path: string,
  options?: RequestOptions,
): Promise<T> {
  const baseUrl = getBaseUrl();
  let url = `${baseUrl}${path}`;

  if (options?.params) {
    const searchParams = new URLSearchParams(options.params);
    url += `?${searchParams.toString()}`;
  }

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  const fetchOptions: RequestInit = {
    method,
    headers,
  };

  if (options?.body !== undefined) {
    fetchOptions.body = JSON.stringify(options.body);
  }

  let res: Response;
  try {
    res = await fetch(url, fetchOptions);
  } catch (err) {
    throw new NetworkError(
      err instanceof Error ? err.message : "Network request failed",
    );
  }

  const json = (await res.json()) as ApiResponse<T>;

  if (!json.ok) {
    throw new ApiError(
      json.error.code,
      json.error.message,
      json.error.type,
      json.error.details,
    );
  }

  return json.data;
}
