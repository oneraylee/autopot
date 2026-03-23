"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { freezeDatasetVersion } from "@/lib/api/dataset";

interface FreezeButtonProps {
  datasetId: string;
  version: number;
  frozen: boolean;
}

export function FreezeButton({ datasetId, version, frozen }: FreezeButtonProps) {
  const [showConfirm, setShowConfirm] = useState(false);
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => freezeDatasetVersion(datasetId, version),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
      setShowConfirm(false);
    },
  });

  if (frozen) {
    return (
      <button disabled className="rounded bg-gray-200 px-3 py-1 text-sm text-gray-500" data-testid="dataset-freeze-btn">
        已冻结
      </button>
    );
  }

  return (
    <>
      <button
        onClick={() => setShowConfirm(true)}
        className="rounded bg-yellow-500 px-3 py-1 text-sm text-white"
        data-testid="dataset-freeze-btn"
      >
        冻结
      </button>

      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="rounded-lg bg-white p-6 shadow-lg">
            <h3 className="text-lg font-semibold">确认冻结</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              冻结版本 {version} 后不可修改，确认操作？
            </p>
            <div className="mt-4 flex gap-2">
              <button
                onClick={() => setShowConfirm(false)}
                className="rounded border px-3 py-1 text-sm"
              >
                取消
              </button>
              <button
                onClick={() => mutation.mutate()}
                disabled={mutation.isPending}
                className="rounded bg-yellow-500 px-3 py-1 text-sm text-white disabled:opacity-50"
              >
                {mutation.isPending ? "冻结中..." : "确认"}
              </button>
            </div>
            {mutation.error && (
              <p className="mt-2 text-sm text-destructive">{mutation.error.message}</p>
            )}
          </div>
        </div>
      )}
    </>
  );
}
