import { z } from "zod";

export const datasetImportSchema = z.object({
  version: z.number().int().positive(),
  manifest_uri: z.string().min(1),
});

export type DatasetImportFormValues = z.infer<typeof datasetImportSchema>;

export const sceneLabelSchema = z
  .object({
    frame_id: z.string().min(1),
    weather: z.string().optional(),
    time_of_day: z.string().optional(),
    road_type: z.string().optional(),
    weather_other_text: z.string().optional(),
  })
  .refine(
    (d) => {
      if (d.weather === "other") {
        return !!d.weather_other_text && d.weather_other_text.length > 0;
      }
      return true;
    },
    {
      message: "weather 为 other 时必须填写 weather_other_text",
      path: ["weather_other_text"],
    },
  );

export type SceneLabelFormValues = z.infer<typeof sceneLabelSchema>;
