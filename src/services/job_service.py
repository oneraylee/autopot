from copy import deepcopy

from repositories.errors import RepositoryError


class JobService:
    def __init__(self, *, job_repository, dataset_repository) -> None:
        self._job_repository = job_repository
        self._dataset_repository = dataset_repository
        self._gpu_locks: dict[str, str] = {}
        self._job_to_gpu: dict[str, str] = {}

    def create_job_draft(self, *, job_id: str, task_type: str, dataset_version_id: str) -> dict:
        self._ensure_frozen_dataset_version(dataset_version_id)
        return self._job_repository.create_job(
            job_id=job_id,
            task_type=task_type,
            dataset_version_id=dataset_version_id,
        )

    def create_and_queue_job(self, *, job_id: str, task_type: str, dataset_version_id: str) -> dict:
        self.create_job_draft(
            job_id=job_id,
            task_type=task_type,
            dataset_version_id=dataset_version_id,
        )
        return self._job_repository.transition_status(job_id, to_status="queued")

    def start_job(self, *, job_id: str, gpu_id: str) -> dict:
        job = self._job_repository.get_job(job_id)
        if job["status"] == "created":
            self._job_repository.transition_status(job_id, to_status="queued")

        holder = self._gpu_locks.get(gpu_id)
        if holder is not None and holder != job_id:
            raise RepositoryError("RESOURCE_LOCKED", f"gpu {gpu_id} already in use")

        self._gpu_locks[gpu_id] = job_id
        self._job_to_gpu[job_id] = gpu_id
        snapshot = self._job_repository.transition_status(job_id, to_status="running")
        self._job_repository.record_resource_usage(
            job_id,
            cpu_cores=1,
            memory_mb=1024,
            gpu_devices=[gpu_id],
        )
        return snapshot

    def finish_job(self, *, job_id: str) -> dict:
        snapshot = self._job_repository.transition_status(job_id, to_status="succeeded")
        self.release_job_resources(job_id=job_id)
        return snapshot

    def fail_job(self, *, job_id: str, reason: str) -> dict:
        _ = reason
        snapshot = self._job_repository.transition_status(job_id, to_status="failed")
        self.release_job_resources(job_id=job_id)
        return snapshot

    def release_job_resources(self, *, job_id: str) -> None:
        gpu_id = self._job_to_gpu.pop(job_id, None)
        if gpu_id is None:
            return
        if self._gpu_locks.get(gpu_id) == job_id:
            self._gpu_locks.pop(gpu_id, None)

    def current_locks(self) -> dict[str, str]:
        return deepcopy(self._gpu_locks)

    def get_job(self, job_id: str) -> dict:
        return self._job_repository.get_job(job_id)

    @staticmethod
    def _parse_dataset_version_id(dataset_version_id: str) -> tuple[str, int]:
        try:
            dataset_id, version_token = dataset_version_id.split(":v", maxsplit=1)
            return dataset_id, int(version_token)
        except ValueError as exc:
            raise RepositoryError("DATA_INVALID", "invalid dataset_version_id") from exc

    def _ensure_frozen_dataset_version(self, dataset_version_id: str) -> None:
        dataset_id, version = self._parse_dataset_version_id(dataset_version_id)
        version_snapshot = self._dataset_repository.get_dataset_version(dataset_id=dataset_id, version=version)
        if version_snapshot.get("frozen") is not True:
            raise RepositoryError("DATA_INVALID", "dataset version must be frozen")
