import re
from dataclasses import dataclass


_RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


@dataclass(frozen=True)
class RunArtifacts:
    base_dir: str
    run_id: str

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("run_id cannot be empty")
        if ".." in self.run_id or "/" in self.run_id or "\\" in self.run_id:
            raise ValueError("run_id contains path traversal pattern")
        if _RUN_ID_PATTERN.fullmatch(self.run_id) is None:
            raise ValueError("run_id contains illegal characters")

    @property
    def run_dir(self) -> str:
        return f"{self.base_dir.rstrip('/')}/{self.run_id}"

    @property
    def weights_dir(self) -> str:
        return f"{self.run_dir}/weights"

    @property
    def eval_dir(self) -> str:
        return f"{self.run_dir}/eval"

    @property
    def evidence_dir(self) -> str:
        return f"{self.run_dir}/evidence"

    @property
    def llm_dir(self) -> str:
        return f"{self.run_dir}/llm"

    @property
    def export_dir(self) -> str:
        return f"{self.run_dir}/export"

    def directories(self) -> dict[str, str]:
        return {
            "run_dir": self.run_dir,
            "weights": self.weights_dir,
            "eval": self.eval_dir,
            "evidence": self.evidence_dir,
            "llm": self.llm_dir,
            "export": self.export_dir,
        }

    def eval_report_path(self) -> str:
        return f"{self.eval_dir}/eval_report.json"

    def evidence_pack_path(self) -> str:
        return f"{self.evidence_dir}/evidence_pack.json"

    def analysis_report_path(self) -> str:
        return f"{self.llm_dir}/analysis_report.md"

    def to_index(self) -> dict[str, str]:
        return {
            "run_id": self.run_id,
            "run_dir": self.run_dir,
            "weights_dir": self.weights_dir,
            "eval_dir": self.eval_dir,
            "evidence_dir": self.evidence_dir,
            "llm_dir": self.llm_dir,
            "export_dir": self.export_dir,
            "eval_report": self.eval_report_path(),
            "evidence_pack": self.evidence_pack_path(),
            "analysis_report": self.analysis_report_path(),
        }
