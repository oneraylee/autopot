import { request } from "./request";

export interface GatewayProvider {
  name: string;
  models: string[];
  status: string;
}

export interface UsageReportParams {
  start_date?: string;
  end_date?: string;
  group_by?: "provider" | "call_type" | "model";
}

export interface UsageReportItem {
  date?: string;
  provider?: string;
  call_type?: string;
  model?: string;
  tokens?: number;
  cost?: number;
  total_calls?: number;
  input_tokens?: number;
  output_tokens?: number;
  cost_estimate?: number;
}

export interface UsageReportResponse {
  items: UsageReportItem[];
  total_tokens: number;
  total_cost: number;
}

export interface CallLogParams {
  page?: number;
  page_size?: number;
  call_type?: string;
  provider?: string;
  status?: string;
}

export interface CallLogItem {
  id: string;
  call_type: string;
  provider: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  latency_ms: number;
  cost: number;
  status: string;
  created_at: string;
}

export interface CallLogResponse {
  items: CallLogItem[];
  page: number;
  page_size: number;
  total: number;
}

export async function listProviders(): Promise<GatewayProvider[]> {
  const data = await request<GatewayProvider[] | { providers?: GatewayProvider[] }>(
    "GET",
    "/llm-gateway/providers",
  );
  return Array.isArray(data) ? data : data.providers ?? [];
}

export async function getUsageReport(
  params: UsageReportParams = {},
): Promise<UsageReportResponse> {
  const data = await request<
    | UsageReportResponse
    | {
        period?: { start?: string; end?: string };
        groups?: UsageReportItem[];
      }
  >("GET", "/llm-gateway/usage", { params: params as Record<string, string> });

  if ("items" in data) {
    return data;
  }

  const items = data.groups ?? [];
  return {
    items,
    total_tokens: items.reduce(
      (sum, item) => sum + (item.tokens ?? item.input_tokens ?? 0) + (item.output_tokens ?? 0),
      0,
    ),
    total_cost: items.reduce((sum, item) => sum + (item.cost ?? item.cost_estimate ?? 0), 0),
  };
}

export async function getCallLogs(
  params: CallLogParams = {},
): Promise<CallLogResponse> {
  const page = params.page ?? 1;
  const pageSize = params.page_size ?? 20;
  const data = await request<
    | CallLogResponse
    | {
        logs?: CallLogItem[];
        total?: number;
      }
  >("GET", "/llm-gateway/call-logs", {
    params: Object.fromEntries(
      Object.entries(params).filter(([, value]) => value !== undefined).map(([key, value]) => [key, String(value)]),
    ),
  });

  if ("items" in data) {
    return data;
  }

  return {
    items: data.logs ?? [],
    page,
    page_size: pageSize,
    total: data.total ?? (data.logs?.length ?? 0),
  };
}