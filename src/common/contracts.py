from dataclasses import dataclass
from typing import Any


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or value.strip() == "":
        raise ValueError(f"{name} is required")


@dataclass(frozen=True)
class JobSpec:
    job_id: str
    task_type: str
    dataset_uri: str
    precision_mode: str

    def __post_init__(self) -> None:
        _require_non_empty("job_id", self.job_id)
        _require_non_empty("task_type", self.task_type)
        _require_non_empty("dataset_uri", self.dataset_uri)
        if self.task_type not in {"TRAINING", "EVALUATION", "ANALYSIS", "EXPORT"}:
            raise ValueError("task_type is invalid")
        if self.precision_mode not in {"fp32", "fp16", "bf16"}:
            raise ValueError("precision_mode is invalid")


@dataclass(frozen=True)
class ProjectKpiConfig:
    primary_kpi: str
    threshold: float
    scenes: list[str]

    def __post_init__(self) -> None:
        _require_non_empty("primary_kpi", self.primary_kpi)
        if not isinstance(self.threshold, (float, int)):
            raise ValueError("threshold must be numeric")
        if not isinstance(self.scenes, list) or not self.scenes:
            raise ValueError("scenes is required")


@dataclass(frozen=True)
class EvalSummary:
    business_kpi: float
    kpi_components: list[dict[str, Any]]
    by_scene: list[dict[str, Any]]

    def __post_init__(self) -> None:
        if not isinstance(self.business_kpi, (float, int)):
            raise ValueError("business_kpi must be numeric")
        if not isinstance(self.kpi_components, list):
            raise ValueError("kpi_components must be list")
        if not isinstance(self.by_scene, list):
            raise ValueError("by_scene must be list")

    def to_payload(self) -> dict[str, Any]:
        return {
            "overall": {
                "business_kpi": self.business_kpi,
                "kpi_components": self.kpi_components,
            },
            "by_scene": self.by_scene,
        }


@dataclass(frozen=True)
class ExportSpec:
    format: str
    include: list[str]
    destination: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty("format", self.format)
        if not isinstance(self.include, list) or not self.include:
            raise ValueError("include is required")
        if self.destination is not None and (not isinstance(self.destination, str) or self.destination == ""):
            raise ValueError("destination must be non-empty string when provided")

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": self.format,
            "include": self.include,
            "destination": self.destination,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ExportSpec":
        return cls(
            format=payload.get("format", ""),
            include=payload.get("include", []),
            destination=payload.get("destination"),
        )


# ──────────────────────────────────────────────
# Knowledge system contract DTOs
# ──────────────────────────────────────────────


@dataclass(frozen=True)
class SkillCardSummary:
    skill_code: str
    name: str
    category: str
    layer: str
    task_type: str
    summary: str
    maturity: str

    def __post_init__(self) -> None:
        _require_non_empty("skill_code", self.skill_code)
        _require_non_empty("name", self.name)
        _require_non_empty("category", self.category)
        _require_non_empty("layer", self.layer)
        _require_non_empty("task_type", self.task_type)
        _require_non_empty("summary", self.summary)
        _require_non_empty("maturity", self.maturity)

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_code": self.skill_code,
            "name": self.name,
            "category": self.category,
            "layer": self.layer,
            "task_type": self.task_type,
            "summary": self.summary,
            "maturity": self.maturity,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SkillCardSummary":
        return cls(
            skill_code=payload.get("skill_code", ""),
            name=payload.get("name", ""),
            category=payload.get("category", ""),
            layer=payload.get("layer", ""),
            task_type=payload.get("task_type", ""),
            summary=payload.get("summary", ""),
            maturity=payload.get("maturity", ""),
        )


@dataclass(frozen=True)
class QuerySignature:
    task_type: str
    model_family: str
    small_object_ratio: float = 0.0
    weak_scenes: list[str] | None = None
    primary_gap: str = ""
    latency_constraint_ms: int | None = None
    gpu_mem_gb: int | None = None
    deployment_required: bool = False

    def __post_init__(self) -> None:
        _require_non_empty("task_type", self.task_type)
        _require_non_empty("model_family", self.model_family)


@dataclass(frozen=True)
class ConflictReport:
    from_skill_code: str
    to_skill_code: str
    relation_type: str
    strength: str
    description: str

    def __post_init__(self) -> None:
        _require_non_empty("from_skill_code", self.from_skill_code)
        _require_non_empty("to_skill_code", self.to_skill_code)
        _require_non_empty("relation_type", self.relation_type)


@dataclass(frozen=True)
class SkillContext:
    selected_techniques: list[str]
    rejected_techniques: list[str]
    query_signature: dict[str, Any]


@dataclass(frozen=True)
class LLMCallRecord:
    call_type: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    cost_estimate: float
    status: str
    context_ref: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty("call_type", self.call_type)
        _require_non_empty("provider", self.provider)
        _require_non_empty("model", self.model)

    def to_dict(self) -> dict[str, Any]:
        return {
            "call_type": self.call_type,
            "provider": self.provider,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "latency_ms": self.latency_ms,
            "cost_estimate": self.cost_estimate,
            "status": self.status,
            "context_ref": self.context_ref,
        }


@dataclass(frozen=True)
class SkillRef:
    skill_code: str
    name: str
    category: str
    layer: str

    def __post_init__(self) -> None:
        _require_non_empty("skill_code", self.skill_code)
        _require_non_empty("name", self.name)
