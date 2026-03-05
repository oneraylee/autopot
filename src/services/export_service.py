from copy import deepcopy

from repositories.errors import RepositoryError


class ExportService:
    _SUPPORTED_BACKENDS = {"tensorrt"}
    _EXPORTABLE_STATUSES = {"succeeded", "eval_succeeded"}

    def __init__(self, *, job_repository, artifact_repository, executor=None) -> None:
        self._job_repository = job_repository
        self._artifact_repository = artifact_repository
        self._executor = executor or (lambda _payload: {"exit_code": 0, "stdout": "", "stderr": ""})

    def create_export_job(self, *, job_id: str, run_id: str, backend: str) -> dict:
        if backend not in self._SUPPORTED_BACKENDS:
            raise RepositoryError("VALIDATION_ERROR", f"backend is not supported: {backend}")

        job_snapshot = self._job_repository.get_job(job_id)
        if job_snapshot["status"] not in self._EXPORTABLE_STATUSES:
            raise RepositoryError("DATA_INVALID", "job status does not allow export")

        return {
            "job_id": job_id,
            "run_id": run_id,
            "backend": backend,
            "status": "created",
        }

    def run_export(self, *, job_id: str, run_id: str, backend: str) -> dict:
        export_job = self.create_export_job(job_id=job_id, run_id=run_id, backend=backend)
        raw = self._executor(export_job)
        exit_code = int(raw.get("exit_code", 1))
        stdout = str(raw.get("stdout", ""))
        stderr = str(raw.get("stderr", ""))

        if exit_code != 0:
            return {
                "ok": False,
                "error_code": "EXPORT_FAILED",
                "stdout": stdout,
                "stderr": stderr,
            }

        engine_locator = str(raw.get("engine_locator", f"outputs/{run_id}/export/model.engine"))
        artifact = self._artifact_repository.register_artifact(
            job_id=job_id,
            run_id=run_id,
            artifact_type="export",
            locator=engine_locator,
        )
        return {
            "ok": True,
            "artifact": artifact,
            "stdout": stdout,
            "stderr": stderr,
        }

    @staticmethod
    def build_deploy_benchmark(*, throughput_fps: float, latency_p95_ms: float, memory_mb: int) -> dict:
        return {
            "throughput_fps": float(throughput_fps),
            "latency_p95_ms": float(latency_p95_ms),
            "memory_mb": int(memory_mb),
            "unit": {
                "throughput_fps": "fps",
                "latency_p95_ms": "ms",
                "memory_mb": "MB",
            },
        }

    @staticmethod
    def merge_deploy_metrics_to_kpi(
        *,
        eval_business_kpi: float,
        deploy_benchmark: dict,
        project_kpi_config: dict,
    ) -> dict:
        weights = deepcopy(project_kpi_config.get("weights", {}))
        eval_weight = float(weights.get("eval", 0.7))
        deploy_weight = float(weights.get("deploy", 0.3))

        constraints = project_kpi_config.get("deploy_constraints", {})
        latency_max_ms = constraints.get("latency_p95_ms_max")
        latency_value = float(deploy_benchmark.get("latency_p95_ms", 0.0))
        constraint_passed = True
        constraint_reason = None
        if latency_max_ms is not None and latency_value > float(latency_max_ms):
            constraint_passed = False
            constraint_reason = "latency_p95_ms exceeds threshold"

        throughput_value = float(deploy_benchmark.get("throughput_fps", 0.0))
        deploy_score = min(1.0, throughput_value / 100.0)
        merged_business_kpi = float(eval_business_kpi) * eval_weight + deploy_score * deploy_weight

        return {
            "merged_business_kpi": merged_business_kpi,
            "constraint_passed": constraint_passed,
            "constraint_reason": constraint_reason,
            "weights": {"eval": eval_weight, "deploy": deploy_weight},
            "deploy_score": deploy_score,
        }
