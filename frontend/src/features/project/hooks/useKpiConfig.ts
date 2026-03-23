import { useQuery } from "@tanstack/react-query";
import { getKpiConfig } from "@/lib/api/project";

export function useKpiConfig(projectId: string) {
  return useQuery({
    queryKey: ["kpi-config", projectId],
    queryFn: () => getKpiConfig(projectId),
    enabled: !!projectId,
  });
}
