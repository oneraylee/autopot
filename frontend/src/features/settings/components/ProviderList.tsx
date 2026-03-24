import type { GatewayProvider } from "@/lib/api/llm-gateway";

interface ProviderListProps {
  providers: GatewayProvider[];
}

export function ProviderList({ providers }: ProviderListProps) {
  if (providers.length === 0) {
    return <div className="p-6 text-muted-foreground">暂无 Provider 数据</div>;
  }

  return (
    <div className="overflow-x-auto" data-testid="provider-list">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-muted-foreground">
            <th className="px-4 py-2">名称</th>
            <th className="px-4 py-2">支持模型</th>
            <th className="px-4 py-2">状态</th>
          </tr>
        </thead>
        <tbody>
          {providers.map((provider) => (
            <tr key={provider.name} className="border-b">
              <td className="px-4 py-2 font-medium">{provider.name}</td>
              <td className="px-4 py-2">{provider.models.join(", ")}</td>
              <td className="px-4 py-2">{provider.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}