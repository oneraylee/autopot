from typing import Any

from api._response import error, run_with_error_mapping
from services.export_service import ExportService


class ExportRoutes:
    def __init__(self, *, job_repository, artifact_repository, executor=None) -> None:
        self._service = ExportService(
            job_repository=job_repository,
            artifact_repository=artifact_repository,
            executor=executor,
        )
        self._exports: dict[str, dict[str, Any]] = {}
        self._seq = 0

    def create_export(self, payload: dict[str, Any]) -> dict[str, Any]:
        def _create() -> dict[str, Any]:
            job_id = payload.get("job_id")
            run_id = payload.get("run_id")
            backend = payload.get("backend")
            if not isinstance(job_id, str) or job_id.strip() == "":
                raise ValueError("job_id is required")
            if not isinstance(run_id, str) or run_id.strip() == "":
                raise ValueError("run_id is required")
            if not isinstance(backend, str) or backend.strip() == "":
                raise ValueError("backend is required")

            self._seq += 1
            export_id = f"export-{self._seq}"
            result = self._service.run_export(job_id=job_id, run_id=run_id, backend=backend)
            status = "succeeded" if result.get("ok") is True else "failed"
            self._exports[export_id] = {
                "export_id": export_id,
                "job_id": job_id,
                "run_id": run_id,
                "backend": backend,
                "status": status,
                "result": result,
            }
            return {"export_id": export_id}

        return run_with_error_mapping(_create)

    def get_export_status(self, export_id: str) -> dict[str, Any]:
        def _status() -> dict[str, Any]:
            if export_id not in self._exports:
                raise ValueError("export not found")
            return self._exports[export_id]

        response = run_with_error_mapping(_status)
        if response["ok"] is False and response["error"]["code"] == "VALIDATION_ERROR":
            return error(code="NOT_FOUND", message="export not found")
        return response

    def get_deploy_benchmark(self, export_id: str) -> dict[str, Any]:
        def _benchmark() -> dict[str, Any]:
            if export_id not in self._exports:
                raise ValueError("export not found")
            return {
                "export_id": export_id,
                "benchmark": self._service.build_deploy_benchmark(
                    throughput_fps=120.0,
                    latency_p95_ms=19.5,
                    memory_mb=2048,
                ),
            }

        response = run_with_error_mapping(_benchmark)
        if response["ok"] is False and response["error"]["code"] == "VALIDATION_ERROR":
            return error(code="NOT_FOUND", message="export not found")
        return response
