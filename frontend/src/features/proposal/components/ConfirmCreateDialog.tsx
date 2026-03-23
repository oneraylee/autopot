"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { createFromProposal } from "@/lib/api/proposal";

interface Candidate {
  name: string;
  changes: unknown[];
}

interface ConfirmCreateDialogProps {
  open: boolean;
  onClose: () => void;
  candidate: Candidate;
  baselineJobId: string;
}

export function ConfirmCreateDialog({
  open,
  onClose,
  candidate,
  baselineJobId,
}: ConfirmCreateDialogProps) {
  const router = useRouter();
  const [who, setWho] = useState("");
  const [when, setWhen] = useState(new Date().toISOString().slice(0, 10));

  const mutation = useMutation({
    mutationFn: () =>
      createFromProposal({
        candidate,
        baseline_job_id: baselineJobId,
        who,
        when,
        confirmed: true,
      }),
    onSuccess: (data) => {
      onClose();
      router.push(`/jobs/${data.job_id}`);
    },
  });

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-lg">
        <h3 className="text-lg font-semibold">候选方案确认</h3>
        <p className="mt-2 text-sm">
          方案: <span className="font-medium">{candidate.name}</span>
        </p>
        <p className="text-sm text-muted-foreground">
          基线任务: {baselineJobId}
        </p>

        <div className="mt-4 space-y-3">
          <div>
            <label htmlFor="confirm-who" className="block text-sm font-medium">
              操作人
            </label>
            <input
              id="confirm-who"
              value={who}
              onChange={(e) => setWho(e.target.value)}
              className="mt-1 block w-full rounded border px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label htmlFor="confirm-when" className="block text-sm font-medium">
              日期
            </label>
            <input
              id="confirm-when"
              type="date"
              value={when}
              onChange={(e) => setWhen(e.target.value)}
              className="mt-1 block w-full rounded border px-3 py-2 text-sm"
            />
          </div>
        </div>

        <div className="mt-4 flex gap-2">
          <button
            onClick={onClose}
            className="rounded border px-3 py-2 text-sm"
          >
            取消
          </button>
          <button
            onClick={() => mutation.mutate()}
            disabled={!who || !when || mutation.isPending}
            className="rounded bg-primary px-3 py-2 text-sm text-primary-foreground disabled:opacity-50"
            data-testid="candidate-create-btn"
          >
            {mutation.isPending ? "创建中..." : "确认创建"}
          </button>
        </div>

        {mutation.error && (
          <p className="mt-2 text-sm text-destructive">{mutation.error.message}</p>
        )}
      </div>
    </div>
  );
}
