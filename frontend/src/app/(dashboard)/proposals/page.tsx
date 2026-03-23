"use client";

import { ValidateForm } from "@/features/proposal/components/ValidateForm";

export default function ProposalsPage() {

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Proposals</h1>
      <p className="text-muted-foreground">验证候选实验并确认创建新任务。</p>

      <section className="rounded-lg border p-4">
        <h2 className="text-lg font-semibold mb-3">验证 Proposal</h2>
        <ValidateForm />
      </section>
    </div>
  );
}
