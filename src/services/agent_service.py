from datetime import UTC, datetime

from common.schema_validators import validate_payload
from repositories.errors import RepositoryError


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class AgentService:
    def __init__(self, create_training_job=None) -> None:
        self._create_training_job = create_training_job

    def analyze(
        self,
        *,
        evidence_pack: dict,
        agent_output: dict,
        baseline: dict | None = None,
        user_confirmed: bool = False,
        job_id: str = "",
        run_id: str = "",
        baseline_job_id: str = "",
    ) -> dict:
        _ = evidence_pack
        if not isinstance(agent_output, dict):
            raise RepositoryError("LLM_FAILED", "agent output must be dict")

        analysis_report = agent_output.get("analysis_report")
        next_experiments = agent_output.get("next_experiments")
        if not isinstance(analysis_report, str) or not isinstance(next_experiments, dict):
            raise RepositoryError("LLM_FAILED", "agent output schema invalid")

        validation = validate_payload("next_experiments", next_experiments)
        if validation["ok"] is not True:
            raise RepositoryError("LLM_FAILED", "next_experiments schema invalid")

        self.validate_candidates(next_experiments=next_experiments, baseline=baseline or {})

        triggered = False
        if user_confirmed and self._create_training_job is not None:
            for candidate in next_experiments.get("experiments", []):
                self._create_training_job(candidate)
            triggered = True

        return {
            "ok": True,
            "analysis_report": analysis_report,
            "next_experiments": next_experiments,
            "job_creation_triggered": triggered,
            "job_id": job_id,
            "run_id": run_id,
            "baseline_job_id": baseline_job_id,
            "status": "success",
            "created_at": _now(),
        }

    @staticmethod
    def validate_candidates(*, next_experiments: dict, baseline: dict) -> None:
        experiments = next_experiments.get("experiments", [])
        for index, candidate in enumerate(experiments):
            evidence_refs = candidate.get("evidence_refs")
            if not isinstance(evidence_refs, list) or not evidence_refs:
                raise RepositoryError("LLM_FAILED", f"candidate[{index}] missing evidence_refs")

            changes = candidate.get("changes")
            if not isinstance(changes, list):
                raise RepositoryError("LLM_FAILED", f"candidate[{index}] changes invalid")

            for change in changes:
                field_name = change.get("field")
                if field_name in baseline and baseline[field_name] != change.get("from"):
                    raise RepositoryError("LLM_FAILED", f"candidate[{index}] is not baseline-relative")
