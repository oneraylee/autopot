from typing import Any

from api._response import error, run_with_error_mapping
from repositories.errors import RepositoryError
from services.agent_service import AgentService


class ProposalRoutes:
    def __init__(self, *, create_training_job) -> None:
        self._create_training_job = create_training_job
        self._agent_service = AgentService(create_training_job=create_training_job)
        self._idem_results: dict[str, dict[str, Any]] = {}

    def validate_proposals(self, payload: dict[str, Any]) -> dict[str, Any]:
        def _validate() -> dict[str, Any]:
            result = self._agent_service.analyze(
                evidence_pack={"kpi_config": {}, "index_paths": {}},
                agent_output=payload,
                user_confirmed=False,
            )
            accepted = len(result["next_experiments"].get("experiments", []))
            return {"accepted": accepted}

        return run_with_error_mapping(_validate)

    def create_from_proposal(self, payload: dict[str, Any]) -> dict[str, Any]:
        def _create() -> dict[str, Any]:
            baseline_job_id = payload.get("baseline_job_id")
            who = payload.get("who")
            when = payload.get("when")
            confirmed = payload.get("confirmed")
            candidate = payload.get("candidate")
            idempotency_key = payload.get("idempotency_key")

            if not isinstance(baseline_job_id, str) or baseline_job_id.strip() == "":
                raise ValueError("baseline_job_id is required")
            if not isinstance(who, str) or who.strip() == "":
                raise ValueError("who is required")
            if not isinstance(when, str) or when.strip() == "":
                raise ValueError("when is required")
            if confirmed is not True:
                raise ValueError("proposal must be confirmed before creation")
            if not isinstance(candidate, dict):
                raise ValueError("candidate is required")
            if isinstance(idempotency_key, str) and idempotency_key in self._idem_results:
                return self._idem_results[idempotency_key]

            self._agent_service.validate_candidates(
                next_experiments={"experiments": [candidate]},
                baseline=payload.get("baseline", {}),
            )
            create_result = self._create_training_job(candidate)
            job_id = create_result.get("job_id", "")
            if not isinstance(job_id, str) or job_id == "":
                raise RepositoryError("SYSTEM_ERROR", "create_training_job must return job_id")

            data = {
                "job_id": job_id,
                "audit": {
                    "who": who,
                    "when": when,
                    "baseline_job_id": baseline_job_id,
                },
            }
            if isinstance(idempotency_key, str) and idempotency_key != "":
                self._idem_results[idempotency_key] = data
            return data

        return run_with_error_mapping(_create)
