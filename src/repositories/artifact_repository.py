from copy import deepcopy
from datetime import UTC, datetime

from .errors import RepositoryError, require_non_empty


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class ArtifactRepository:
    _ALLOWED_TYPES = {"weights", "eval", "evidence", "llm", "export"}

    def __init__(self) -> None:
        self._artifacts: list[dict] = []
        self._id = 0

    def validate_artifact_path(self, locator: str) -> str:
        require_non_empty(locator, field_name="locator")
        if "://" in locator:
            if locator.startswith(("s3://", "oss://", "gs://")):
                return "object_id"
            raise RepositoryError("VALIDATION_ERROR", "unsupported object locator scheme")

        if locator.startswith("/"):
            raise RepositoryError("VALIDATION_ERROR", "absolute path is not allowed")
        if ".." in locator.split("/"):
            raise RepositoryError("VALIDATION_ERROR", "path traversal is not allowed")
        return "relative_path"

    def register_artifact(self, *, job_id: str, run_id: str, artifact_type: str, locator: str) -> dict:
        require_non_empty(job_id, field_name="job_id")
        require_non_empty(run_id, field_name="run_id")
        if artifact_type not in self._ALLOWED_TYPES:
            raise RepositoryError("VALIDATION_ERROR", "artifact_type is invalid")
        locator_type = self.validate_artifact_path(locator)

        self._id += 1
        record = {
            "artifact_id": f"artifact-{self._id}",
            "job_id": job_id,
            "run_id": run_id,
            "artifact_type": artifact_type,
            "locator": locator,
            "locator_type": locator_type,
            "created_at": _now(),
        }
        self._artifacts.append(record)
        return deepcopy(record)

    def list_artifacts(self, *, job_id: str, run_id: str | None = None, artifact_type: str | None = None) -> list[dict]:
        require_non_empty(job_id, field_name="job_id")
        result = [item for item in self._artifacts if item["job_id"] == job_id]
        if run_id is not None:
            result = [item for item in result if item["run_id"] == run_id]
        if artifact_type is not None:
            result = [item for item in result if item["artifact_type"] == artifact_type]
        return deepcopy(result)
