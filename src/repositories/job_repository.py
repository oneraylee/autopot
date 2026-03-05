from copy import deepcopy
from datetime import UTC, datetime

from common.domain_types import JobStatus, TaskType

from .errors import RepositoryError, require_non_empty


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class JobRepository:
    _ALLOWED_TRANSITIONS = {
        JobStatus.CREATED.value: {JobStatus.QUEUED.value},
        JobStatus.QUEUED.value: {JobStatus.RUNNING.value, JobStatus.CANCELED.value},
        JobStatus.RUNNING.value: {JobStatus.SUCCEEDED.value, JobStatus.FAILED.value, JobStatus.CANCELED.value},
        JobStatus.SUCCEEDED.value: {JobStatus.EVALUATING.value},
        JobStatus.EVALUATING.value: {JobStatus.EVAL_SUCCEEDED.value, JobStatus.EVAL_FAILED.value},
        JobStatus.EVAL_SUCCEEDED.value: {JobStatus.EVIDENCE_READY.value},
        JobStatus.EVIDENCE_READY.value: {JobStatus.LLM_ANALYZING.value},
        JobStatus.LLM_ANALYZING.value: {JobStatus.LLM_DONE.value, JobStatus.LLM_FAILED.value},
    }

    def __init__(self) -> None:
        self._jobs: dict[str, dict] = {}
        self._events: dict[str, list[dict]] = {}
        self._resources: dict[str, list[dict]] = {}

    def create_job(self, *, job_id: str, task_type: str, dataset_version_id: str) -> dict:
        require_non_empty(job_id, field_name="job_id")
        require_non_empty(dataset_version_id, field_name="dataset_version_id")
        require_non_empty(task_type, field_name="task_type")
        if task_type not in {item.value for item in TaskType}:
            raise RepositoryError("VALIDATION_ERROR", "task_type is invalid")
        if job_id in self._jobs:
            raise RepositoryError("CONFLICT", "job already exists")

        timestamp = _now()
        record = {
            "job_id": job_id,
            "task_type": task_type,
            "dataset_version_id": dataset_version_id,
            "status": JobStatus.CREATED.value,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        self._jobs[job_id] = record
        self._events[job_id] = []
        self._resources[job_id] = []
        self._append_event(job_id=job_id, from_status=None, to_status=JobStatus.CREATED.value)
        return deepcopy(record)

    def get_job(self, job_id: str) -> dict:
        job = self._jobs.get(job_id)
        if job is None:
            raise RepositoryError("NOT_FOUND", "job not found")
        return deepcopy(job)

    def transition_status(self, job_id: str, *, to_status: str) -> dict:
        job = self._jobs.get(job_id)
        if job is None:
            raise RepositoryError("NOT_FOUND", "job not found")

        current = job["status"]
        allowed = self._ALLOWED_TRANSITIONS.get(current, set())
        if to_status not in allowed:
            raise RepositoryError("INVALID_TRANSITION", f"cannot transition {current} -> {to_status}")

        job["status"] = to_status
        job["updated_at"] = _now()
        self._append_event(job_id=job_id, from_status=current, to_status=to_status)
        return deepcopy(job)

    def append_status_event(self, job_id: str, *, to_status: str) -> dict:
        job = self._jobs.get(job_id)
        if job is None:
            raise RepositoryError("NOT_FOUND", "job not found")
        return self._append_event(job_id=job_id, from_status=job["status"], to_status=to_status)

    def list_events(self, job_id: str) -> list[dict]:
        if job_id not in self._jobs:
            raise RepositoryError("NOT_FOUND", "job not found")
        return deepcopy(self._events[job_id])

    def record_resource_usage(self, job_id: str, *, cpu_cores: int, memory_mb: int, gpu_devices: list[str]) -> dict:
        if job_id not in self._jobs:
            raise RepositoryError("NOT_FOUND", "job not found")
        if not isinstance(cpu_cores, int) or cpu_cores <= 0:
            raise RepositoryError("VALIDATION_ERROR", "cpu_cores must be positive int")
        if not isinstance(memory_mb, int) or memory_mb <= 0:
            raise RepositoryError("VALIDATION_ERROR", "memory_mb must be positive int")
        if not isinstance(gpu_devices, list):
            raise RepositoryError("VALIDATION_ERROR", "gpu_devices must be list")

        sequence = len(self._resources[job_id]) + 1
        record = {
            "job_id": job_id,
            "sequence": sequence,
            "cpu_cores": cpu_cores,
            "memory_mb": memory_mb,
            "gpu_devices": list(gpu_devices),
            "recorded_at": _now(),
        }
        self._resources[job_id].append(record)
        return deepcopy(record)

    def get_resource_records(self, job_id: str) -> list[dict]:
        if job_id not in self._jobs:
            raise RepositoryError("NOT_FOUND", "job not found")
        return deepcopy(self._resources[job_id])

    def _append_event(self, *, job_id: str, from_status: str | None, to_status: str) -> dict:
        sequence = len(self._events[job_id]) + 1
        event = {
            "job_id": job_id,
            "sequence": sequence,
            "from_status": from_status,
            "to_status": to_status,
            "created_at": _now(),
        }
        self._events[job_id].append(event)
        return deepcopy(event)
