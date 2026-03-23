"use client";

import type { EvalReportPayload } from "@/lib/api/analysis";

interface EvalReportProps {
  data: EvalReportPayload;
}

export function EvalReport({ data }: EvalReportProps) {
  const { overall, by_class, by_scene } = data;

  return (
    <div className="space-y-6">
      {/* Overall KPI */}
      <section>
        <h3 className="text-lg font-semibold mb-2">business_kpi</h3>
        <p className="text-3xl font-bold">{overall.business_kpi}</p>
        {Object.keys(overall.kpi_components).length > 0 && (
          <table className="mt-3 w-full text-sm border-collapse">
            <thead>
              <tr className="border-b">
                <th className="text-left py-1">指标</th>
                <th className="text-right py-1">值</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(overall.kpi_components).map(([k, v]) => (
                <tr key={k} className="border-b">
                  <td className="py-1">{k}</td>
                  <td className="text-right py-1">{v}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {/* By Class */}
      {by_class.length > 0 && (
        <section>
          <h3 className="text-lg font-semibold mb-2">By Class</h3>
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b">
                {Object.keys(by_class[0]).map((key) => (
                  <th key={key} className="text-left py-1">{key}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {by_class.map((row, i) => (
                <tr key={i} className="border-b">
                  {Object.values(row).map((val, j) => (
                    <td key={j} className="py-1">{String(val)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {/* By Scene */}
      {by_scene.length > 0 && (
        <section>
          <h3 className="text-lg font-semibold mb-2">By Scene</h3>
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b">
                {Object.keys(by_scene[0].scene).map((k) => (
                  <th key={k} className="text-left py-1">{k}</th>
                ))}
                <th className="text-right py-1">KPI</th>
                <th className="text-right py-1">FN</th>
                <th className="text-right py-1">FP</th>
              </tr>
            </thead>
            <tbody>
              {by_scene.map((row, i) => (
                <tr key={i} className="border-b">
                  {Object.values(row.scene).map((v, j) => (
                    <td key={j} className="py-1">{v}</td>
                  ))}
                  <td className="text-right py-1">{row.kpi}</td>
                  <td className="text-right py-1">{row.fn}</td>
                  <td className="text-right py-1">{row.fp}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}
