from typing import Any

from api._response import run_with_error_mapping


class JobRoutes:
    def __init__(self, *, job_service, job_repository) -> None:
        self._job_service = job_service
        self._job_repository = job_repository
        self._logs: dict[str, list[dict[str, Any]]] = {}
        self._metrics: dict[str, list[dict[str, Any]]] = {}

    def create_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        def _create() -> dict[str, Any]:
            resources = payload.get("resources", {})
            gpu_count = resources.get("gpu_count")
            if not isinstance(gpu_count, int) or gpu_count <= 0:
                raise ValueError("resources.gpu_count must be positive int")
            return self._job_service.create_and_queue_job(
                job_id=str(payload.get("job_id", "")),
                task_type=str(payload.get("task_type", "")),
                dataset_version_id=str(payload.get("dataset_version_id", "")),
            )

        return run_with_error_mapping(_create)

    def get_job(self, job_id: str) -> dict[str, Any]:
        return run_with_error_mapping(lambda: self._job_repository.get_job(job_id))

    def start_job(self, job_id: str, *, gpu_id: str) -> dict[str, Any]:
        return run_with_error_mapping(lambda: self._job_service.start_job(job_id=job_id, gpu_id=gpu_id))

    def append_log(self, job_id: str, message: str) -> None:
        records = self._logs.setdefault(job_id, [])
        records.append({"line": len(records) + 1, "message": message})

    def get_logs(self, job_id: str, *, page: int, page_size: int) -> dict[str, Any]:
        def _list() -> dict[str, Any]:
            if page <= 0 or page_size <= 0:
                raise ValueError("page and page_size must be positive")
            records = self._logs.get(job_id, [])
            start = (page - 1) * page_size
            end = start + page_size
            return {
                "items": records[start:end],
                "page": page,
                "page_size": page_size,
                "total": len(records),
            }

        return run_with_error_mapping(_list)

    def record_metric(self, job_id: str, *, ts: int, values: dict[str, Any]) -> None:
        records = self._metrics.setdefault(job_id, [])
        records.append({"ts": ts, "values": values})

    def get_metrics(self, job_id: str, *, start_ts: int, end_ts: int) -> dict[str, Any]:
        def _list() -> dict[str, Any]:
            if end_ts < start_ts:
                raise ValueError("invalid time window")
            records = self._metrics.get(job_id, [])
            items = [item for item in records if start_ts <= item["ts"] <= end_ts]
            return {
                "items": items,
                "window": {"start_ts": start_ts, "end_ts": end_ts},
            }

        return run_with_error_mapping(_list)
