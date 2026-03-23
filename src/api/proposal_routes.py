from typing import Any

from api._response import error, run_with_error_mapping
from repositories.errors import RepositoryError
from services.agent_service import AgentService


class ProposalRoutes:
    def __init__(self, *, create_training_job, artifact_repository=None) -> None:
        self._create_training_job = create_training_job
        self._agent_service = AgentService(create_training_job=create_training_job)
        self._idem_results: dict[str, dict[str, Any]] = {}
        self._artifact_repository = artifact_repository
        self._payload_by_key: dict[str, dict[str, Any]] = {}

    def register_artifact_payload(
        self,
        *,
        job_id: str,
        run_id: str,
        artifact_type: str,
        payload: dict[str, Any],
    ) -> None:
        key = f"{job_id}:{run_id}:{artifact_type}"
        self._payload_by_key[key] = payload

    def validate_proposals(self, payload: dict[str, Any]) -> dict[str, Any]:
        job_id = payload.get("job_id")
        run_id = payload.get("run_id")

        if isinstance(job_id, str) and isinstance(run_id, str) and self._artifact_repository is not None:
            return self._validate_from_artifacts(job_id, run_id)

        def _validate() -> dict[str, Any]:
            result = self._agent_service.analyze(
                evidence_pack={"kpi_config": {}, "index_paths": {}},
                agent_output=payload,
                user_confirmed=False,
            )
            accepted = len(result["next_experiments"].get("experiments", []))
            return {"accepted": accepted}

        return run_with_error_mapping(_validate)

    def _validate_from_artifacts(self, job_id: str, run_id: str) -> dict[str, Any]:
        def _resolve() -> dict[str, Any]:
            artifacts = self._artifact_repository.list_artifacts(
                job_id=job_id, run_id=run_id, artifact_type="llm"
            )
            if not artifacts:
                raise RepositoryError("NOT_FOUND", "llm artifact not found for this job/run")

            artifact = artifacts[-1]
            key = f"{job_id}:{run_id}:llm"
            agent_output = self._payload_by_key.get(key)
            if agent_output is None:
                raise RepositoryError("NOT_FOUND", "artifact payload not found")

            next_experiments = agent_output.get("next_experiments")
            if not isinstance(next_experiments, dict):
                raise RepositoryError("DATA_INVALID", "next_experiments missing")

            self._agent_service.validate_candidates(
                next_experiments=next_experiments, baseline={}
            )

            candidates = next_experiments.get("experiments", [])
            return {
                "accepted": len(candidates),
                "baseline_job_id": job_id,
                "candidates": candidates,
            }

        return run_with_error_mapping(_resolve)

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
            create_result = self._create_training_job(
                {
                    "baseline_job_id": baseline_job_id,
                    "candidate": candidate,
                    "who": who,
                    "when": when,
                }
            )
            job_id = create_result.get("job_id", "")
            if not isinstance(job_id, str) or job_id == "":
                raise RepositoryError("SYSTEM_ERROR", "create_training_job must return job_id")

            data = {
                "job_id": job_id,
                "status": create_result.get("status", "created"),
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
