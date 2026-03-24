import { z } from "zod";

// ──────────────────────────────────────────────────
// createSourceSchema
// ──────────────────────────────────────────────────
export const createSourceSchema = z
  .object({
    source_type: z.enum(["local", "web", "official_doc", "internal_experiment"], {
      errorMap: () => ({
        message:
          "来源类型须为 local / web / official_doc / internal_experiment 之一",
      }),
    }),
    name: z.string().min(1, "来源名称为必填"),
    uri: z.string().min(1, "URI 为必填"),
    author: z.string().optional(),
    license: z.string().optional(),
    trust_level: z
      .number()
      .int()
      .min(1, "信任等级最低为 1")
      .max(5, "信任等级最高为 5"),
  })
  .refine(
    (data) => {
      if (data.source_type === "web") {
        try {
          new URL(data.uri);
          return true;
        } catch {
          return false;
        }
      }
      return true;
    },
    {
      message: "web 类型的来源 URI 必须是合法的 URL",
      path: ["uri"],
    },
  );

export type CreateSourceFormValues = z.infer<typeof createSourceSchema>;

// ──────────────────────────────────────────────────
// importDocumentSchema
// ──────────────────────────────────────────────────
export const importDocumentSchema = z.object({
  source_id: z.string().min(1, "来源 ID 为必填"),
  title: z.string().min(1, "文档标题为必填"),
  doc_type: z.enum(["markdown", "html", "pdf", "note"], {
    errorMap: () => ({
      message: "文档类型须为 markdown / html / pdf / note 之一",
    }),
  }),
  version_label: z.string().optional(),
  language: z.string().optional(),
  content: z.string().optional(),
  url: z.string().url("URL 格式不合法").optional().or(z.literal("")),
});

export type ImportDocumentFormValues = z.infer<typeof importDocumentSchema>;

// ──────────────────────────────────────────────────
// createTechniqueSchema
// ──────────────────────────────────────────────────
export const createTechniqueSchema = z.object({
  skill_code: z
    .string()
    .min(1, "技能编码为必填")
    .regex(
      /^[a-z0-9_]+\.[a-z0-9_]+\.[a-z0-9_]+$/,
      "技能编码格式为 层级.类别.名称，仅允许小写字母、数字和下划线",
    ),
  name: z.string().min(1, "技能名称为必填"),
  category: z.enum(["training", "model", "data", "eval_deploy"], {
    errorMap: () => ({
      message: "分类须为 training / model / data / eval_deploy 之一",
    }),
  }),
  layer: z.string().min(1, "层级为必填"),
  task_type: z.enum(["det", "seg", "cls", "multi"], {
    errorMap: () => ({
      message: "任务类型须为 det / seg / cls / multi 之一",
    }),
  }),
  summary: z.string().optional(),
  rationale: z.string().optional(),
  maturity: z
    .enum(["draft", "reviewed", "verified", "deprecated"])
    .optional(),
});

export type CreateTechniqueFormValues = z.infer<typeof createTechniqueSchema>;
