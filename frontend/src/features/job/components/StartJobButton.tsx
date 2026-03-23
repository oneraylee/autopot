"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { startJob } from "@/lib/api/job";
import type { JobStatus } from "@/lib/api/job";

interface StartJobButtonProps {
  jobId: string;
  status: JobStatus;
}

const startableStatuses: JobStatus[] = ["created", "queued"];

export function StartJobButton({ jobId, status }: StartJobButtonProps) {
  const [gpuId, setGpuId] = useState("");
  const queryClient = useQueryClient();
  const canStart = startableStatuses.includes(status);

  const mutation = useMutation({
    mutationFn: () => startJob(jobId, { gpu_id: gpuId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["job", jobId] });
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });

  return (
    <div className="flex items-center gap-2">
      <input
        type="text"
        placeholder="GPU ID"
        value={gpuId}
        onChange={(e) => setGpuId(e.target.value)}
        className="rounded border px-3 py-1 text-sm"
        disabled={!canStart}
      />
      <button
        onClick={() => mutation.mutate()}
        disabled={!canStart || !gpuId || mutation.isPending}
        className="rounded bg-blue-600 px-3 py-1 text-sm text-white disabled:opacity-50"
        data-testid="job-start-btn"
      >
        {!canStart ? status : mutation.isPending ? "启动中..." : "启动"}
      </button>
      {mutation.error && (
        <span className="text-sm text-destructive">{mutation.error.message}</span>
      )}
    </div>
  );
}
