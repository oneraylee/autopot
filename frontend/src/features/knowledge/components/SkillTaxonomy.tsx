"use client";

import type { SkillCategory } from "@/features/knowledge/types";

const TAXONOMY = [
  {
    label: "Training Skills",
    category: "training" as SkillCategory,
    sublayers: [
      "optimizer",
      "schedule",
      "augment",
      "regularization",
      "precision",
      "freeze",
      "hyperparameter",
      "distributed",
    ],
  },
  {
    label: "Model Skills",
    category: "model" as SkillCategory,
    sublayers: [
      "backbone",
      "neck",
      "head",
      "block",
      "attention",
      "conv",
      "loss",
    ],
  },
  {
    label: "Data Skills",
    category: "data" as SkillCategory,
    sublayers: [
      "cleaning",
      "balancing",
      "scene_coverage",
      "split",
      "preprocessing",
    ],
  },
  {
    label: "Eval & Deploy Skills",
    category: "eval_deploy" as SkillCategory,
    sublayers: ["metric", "calibration", "quantization", "export", "benchmark"],
  },
];

interface SkillTaxonomyProps {
  onCategorySelect?: (filter: { category: SkillCategory; layer?: string }) => void;
}

export function SkillTaxonomy({ onCategorySelect }: SkillTaxonomyProps) {
  return (
    <div className="space-y-2" data-testid="skill-taxonomy">
      {TAXONOMY.map((group) => (
        <div key={group.category} className="rounded border">
          <button
            className="flex w-full items-center justify-between px-3 py-2 text-sm font-medium hover:bg-accent"
            onClick={() =>
              onCategorySelect?.({ category: group.category })
            }
          >
            {group.label}
          </button>
          <div className="grid grid-cols-2 gap-1 px-3 pb-2">
            {group.sublayers.map((layer) => (
              <button
                key={layer}
                className="rounded px-2 py-1 text-xs text-muted-foreground hover:bg-accent text-left"
                onClick={() =>
                  onCategorySelect?.({
                    category: group.category,
                    layer,
                  })
                }
              >
                {layer}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
