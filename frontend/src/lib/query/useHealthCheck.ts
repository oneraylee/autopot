import { useQuery } from "@tanstack/react-query";
import { request } from "@/lib/api/request";

export function useHealthCheck() {
  const query = useQuery({
    queryKey: ["health"],
    queryFn: () => request<{ status: string }>("GET", "/health"),
    refetchInterval: 30_000,
    retry: false,
  });

  return {
    isConnected: query.isSuccess,
    isLoading: query.isLoading,
    error: query.error ?? null,
  };
}
