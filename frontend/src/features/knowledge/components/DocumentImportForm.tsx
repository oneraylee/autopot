"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  importDocumentSchema,
  type ImportDocumentFormValues,
} from "@/schemas/knowledge";
import { knowledgeApi } from "@/lib/api/knowledge";

interface DocumentImportFormProps {
  sourceId: string;
  onSuccess?: () => void;
}

export function DocumentImportForm({ sourceId, onSuccess }: DocumentImportFormProps) {
  const queryClient = useQueryClient();
  const [fileError, setFileError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setValue,
    getValues,
  } = useForm<ImportDocumentFormValues>({
    resolver: zodResolver(importDocumentSchema),
    defaultValues: { source_id: sourceId, doc_type: "markdown" },
  });

  const mutation = useMutation({
    mutationFn: knowledgeApi.importDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledge", "documents", sourceId] });
      reset({ source_id: sourceId, doc_type: "markdown" });
      onSuccess?.();
    },
  });

  return (
    <form
      onSubmit={handleSubmit((data) => mutation.mutate(data))}
      className="space-y-4"
    >
      <div>
        <label htmlFor="title" className="block text-sm font-medium">
          文档标题
        </label>
        <input
          id="title"
          {...register("title")}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm"
        />
        {errors.title && (
          <p className="mt-1 text-sm text-destructive">{errors.title.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="doc_type" className="block text-sm font-medium">
          文档类型
        </label>
        <select
          id="doc_type"
          {...register("doc_type")}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm"
        >
          <option value="markdown">markdown</option>
          <option value="html">html</option>
          <option value="pdf">pdf</option>
          <option value="note">note</option>
        </select>
        {errors.doc_type && (
          <p className="mt-1 text-sm text-destructive">{errors.doc_type.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="url" className="block text-sm font-medium">
          URL（可选，web 来源）
        </label>
        <input
          id="url"
          {...register("url")}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm"
        />
        {errors.url && (
          <p className="mt-1 text-sm text-destructive">{errors.url.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="file" className="block text-sm font-medium">
          本地文件上传
        </label>
        <input
          id="file"
          type="file"
          className="mt-1 block w-full text-sm"
          onChange={async (event) => {
            const file = event.target.files?.[0];
            if (!file) {
              setValue("content", undefined);
              setFileError(null);
              return;
            }

            try {
              const content = await file.text();
              setValue("content", content, { shouldValidate: true });
              if (!getValues("title")) {
                setValue("title", file.name, { shouldValidate: true });
              }
              setFileError(null);
            } catch {
              setValue("content", undefined);
              setFileError("读取本地文件失败");
            }
          }}
        />
        {fileError && (
          <p className="mt-1 text-sm text-destructive">{fileError}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={mutation.isPending}
        className="rounded bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50"
        data-testid="import-document-btn"
      >
        {mutation.isPending ? "导入中..." : "导入文档"}
      </button>

      {mutation.error && (
        <p className="text-sm text-destructive">{mutation.error.message}</p>
      )}
    </form>
  );
}
