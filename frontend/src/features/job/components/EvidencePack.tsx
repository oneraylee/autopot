"use client";

interface EvidencePackData {
  summary: string;
  artifact_index: string[];
  kpi_config: Record<string, unknown>;
}

interface EvidencePackProps {
  data: EvidencePackData;
}

export function EvidencePack({ data }: EvidencePackProps) {
  const { summary, artifact_index, kpi_config } = data;

  return (
    <div className="space-y-6">
      {/* Summary */}
      <section>
        <h3 className="text-lg font-semibold mb-2">摘要</h3>
        <p className="text-sm text-muted-foreground">{summary}</p>
      </section>

      {/* Artifact Index */}
      <section>
        <h3 className="text-lg font-semibold mb-2">产物索引</h3>
        {artifact_index.length === 0 ? (
          <p className="text-sm text-muted-foreground">暂无产物</p>
        ) : (
          <ul className="space-y-1">
            {artifact_index.map((path) => (
              <li key={path} className="text-sm font-mono">{path}</li>
            ))}
          </ul>
        )}
      </section>

      {/* KPI Config */}
      {Object.keys(kpi_config).length > 0 && (
        <section>
          <h3 className="text-lg font-semibold mb-2">KPI 配置</h3>
          {Object.entries(kpi_config).map(([section, values]) => (
            <div key={section} className="mb-3">
              <h4 className="text-sm font-medium mb-1">{section}</h4>
              {typeof values === "object" && values !== null ? (
                <table className="w-full text-sm border-collapse">
                  <tbody>
                    {Object.entries(values as Record<string, unknown>).map(([k, v]) => (
                      <tr key={k} className="border-b">
                        <td className="py-1">{k}</td>
                        <td className="text-right py-1">{String(v)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="text-sm">{String(values)}</p>
              )}
            </div>
          ))}
        </section>
      )}
    </div>
  );
}
