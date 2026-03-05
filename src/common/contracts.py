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
