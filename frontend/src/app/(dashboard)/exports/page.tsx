"use client";

import { CreateExportForm } from "@/features/export/components/CreateExportForm";
import { useState } from "react";
import { ExportStatus } from "@/features/export/components/ExportStatus";
import { DeployBenchmarkView } from "@/features/export/components/DeployBenchmark";

export default function ExportsPage() {
  const [exportId, setExportId] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Exports</h1>
      <p className="text-muted-foreground">创建模型导出并查看部署基准。</p>

      <section className="rounded-lg border p-4">
        <h2 className="text-lg font-semibold mb-3">创建导出</h2>
        <CreateExportForm onSuccess={(id) => setExportId(id)} />
      </section>

      {exportId && (
        <>
          <section className="rounded-lg border p-4">
            <ExportStatus exportId={exportId} />
          </section>
          <section className="rounded-lg border p-4">
            <DeployBenchmarkView exportId={exportId} />
          </section>
        </>
      )}
    </div>
  );
}
