from typing import Any

from api._response import error, run_with_error_mapping
from common.schema_validators import validate_payload


class AnalysisRoutes:
    _EVIDENCE_READY_STATUSES = {"evidence_ready", "llm_analyzing", "llm_done", "llm_failed"}

    def __init__(self, *, job_repository, artifact_repository) -> None:
        self._job_repository = job_repository
        self._artifact_repository = artifact_repository
        self._payload_by_artifact_id: dict[str, dict[str, Any]] = {}

    def register_artifact_payload(
        self,
        *,
        job_id: str,
        run_id: str,
        artifact_type: str,
        locator: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        artifact = self._artifact_repository.register_artifact(
            job_id=job_id,
            run_id=run_id,
            artifact_type=artifact_type,
            locator=locator,
        )
        self._payload_by_artifact_id[artifact["artifact_id"]] = payload
        return artifact

    def get_eval_report(self, job_id: str, *, run_id: str) -> dict[str, Any]:
        return self._resolve_payload(job_id=job_id, run_id=run_id, artifact_type="eval", kind="eval_report", field=None)

    def get_evidence_pack(self, job_id: str, *, run_id: str) -> dict[str, Any]:
        snapshot = self._job_repository.get_job(job_id)
        if snapshot["status"] not in self._EVIDENCE_READY_STATUSES:
            return error(code="DATA_INVALID", message="job stage not ready for evidence_pack")
        return self._resolve_payload(job_id=job_id, run_id=run_id, artifact_type="evidence", kind="evidence_pack", field=None)

    def get_analysis_report(self, job_id: str, *, run_id: str) -> dict[str, Any]:
        return self._resolve_payload(job_id=job_id, run_id=run_id, artifact_type="llm", kind=None, field="analysis_report")

    def get_next_experiments(self, job_id: str, *, run_id: str) -> dict[str, Any]:
        return self._resolve_payload(
            job_id=job_id,
            run_id=run_id,
            artifact_type="llm",
            kind="next_experiments",
            field="next_experiments",
        )

    def _resolve_payload(
        self,
        *,
        job_id: str,
        run_id: str,
        artifact_type: str,
        kind: str | None,
        field: str | None,
    ) -> dict[str, Any]:
        def _resolve() -> dict[str, Any]:
            artifacts = self._artifact_repository.list_artifacts(job_id=job_id, run_id=run_id, artifact_type=artifact_type)
            if not artifacts:
                raise ValueError("artifact not found")
            artifact = artifacts[-1]
            payload = self._payload_by_artifact_id.get(artifact["artifact_id"])
            if payload is None:
                raise ValueError("artifact payload not found")
            content = payload.get(field) if field is not None else payload
            if kind is not None:
                validation = validate_payload(kind, content)
                if validation["ok"] is not True:
                    return {
                        "__error__": True,
                        "code": "DATA_INVALID",
                        "message": f"{kind} payload invalid",
                        "details": validation.get("errors", []),
                    }
            return {
                "job_id": job_id,
                "run_id": run_id,
                "artifact_type": artifact_type,
                "locator": artifact["locator"],
                "locator_type": artifact["locator_type"],
                "payload": content,
            }

        response = run_with_error_mapping(_resolve)
        if response["ok"] and response["data"].get("__error__") is True:
            inner = response["data"]
            return error(code=inner["code"], message=inner["message"], details=inner["details"])
        if response["ok"] is False and response["error"]["code"] == "VALIDATION_ERROR":
            return error(code="NOT_FOUND", message=response["error"]["message"])
        return response
