"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { upsertSceneLabels } from "@/lib/api/dataset";

interface SceneLabelEditorProps {
  datasetVersionId: string;
}

export function SceneLabelEditor({ datasetVersionId }: SceneLabelEditorProps) {
  const [imageId, setImageId] = useState("");
  const [timeOfDay, setTimeOfDay] = useState("");
  const [weather, setWeather] = useState("");
  const [environment, setEnvironment] = useState("");
  const [weatherOtherText, setWeatherOtherText] = useState("");
  const [error, setError] = useState("");

  const mutation = useMutation({
    mutationFn: (labels: Array<Record<string, string>>) =>
      upsertSceneLabels(datasetVersionId, labels),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (weather === "other" && !weatherOtherText.trim()) {
      setError("必填");
      return;
    }
    const label: Record<string, string> = {
      image_id: imageId,
      time_of_day: timeOfDay,
      weather,
      environment,
    };
    if (weather === "other") {
      label.weather_other_text = weatherOtherText;
    }
    mutation.mutate([label]);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="scene-image-id" className="block text-sm font-medium">图片 ID</label>
        <input id="scene-image-id" value={imageId} onChange={(e) => setImageId(e.target.value)}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm" />
      </div>

      <div>
        <label htmlFor="scene-tod" className="block text-sm font-medium">时间段</label>
        <select id="scene-tod" value={timeOfDay} onChange={(e) => setTimeOfDay(e.target.value)}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm">
          <option value="">请选择</option>
          <option value="day">day</option>
          <option value="night">night</option>
          <option value="dawn_dusk">dawn_dusk</option>
        </select>
      </div>

      <div>
        <label htmlFor="scene-weather" className="block text-sm font-medium">天气</label>
        <select id="scene-weather" value={weather} onChange={(e) => setWeather(e.target.value)}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm">
          <option value="">请选择</option>
          <option value="sunny">sunny</option>
          <option value="rain">rain</option>
          <option value="snow">snow</option>
          <option value="fog">fog</option>
          <option value="other">other</option>
        </select>
      </div>

      {weather === "other" && (
        <div>
          <label htmlFor="scene-weather-other" className="block text-sm font-medium">其他天气描述</label>
          <input id="scene-weather-other" value={weatherOtherText}
            onChange={(e) => setWeatherOtherText(e.target.value)}
            className="mt-1 block w-full rounded border px-3 py-2 text-sm" />
        </div>
      )}

      <div>
        <label htmlFor="scene-env" className="block text-sm font-medium">环境</label>
        <select id="scene-env" value={environment} onChange={(e) => setEnvironment(e.target.value)}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm">
          <option value="">请选择</option>
          <option value="outdoor">outdoor</option>
          <option value="indoor">indoor</option>
          <option value="parking">parking</option>
        </select>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <button type="submit" disabled={mutation.isPending}
        className="rounded bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50">
        {mutation.isPending ? "保存中..." : "保存"}
      </button>
    </form>
  );
}
