from repositories.artifact_repository import ArtifactRepository
from repositories.dataset_repository import DatasetRepository
from repositories.job_repository import JobRepository
from services.job_service import JobService


def _build_routes(executor=None):
    from api.export_routes import ExportRoutes

    dataset_repo = DatasetRepository()
    job_repo = JobRepository()
    artifact_repo = ArtifactRepository()

    dataset_repo.create_dataset(dataset_id="ds-1", project_id="proj-1", name="raw")
    dataset_repo.create_dataset_version(dataset_id="ds-1", version=1, manifest_uri="s3://bucket/v1.json")
    dataset_repo.freeze_version(dataset_id="ds-1", version=1)
    service = JobService(job_repository=job_repo, dataset_repository=dataset_repo)
    service.create_and_queue_job(job_id="job-1", task_type="training", dataset_version_id="ds-1:v1")
    service.start_job(job_id="job-1", gpu_id="0")
    service.finish_job(job_id="job-1")

    return ExportRoutes(job_repository=job_repo, artifact_repository=artifact_repo, executor=executor)


def test_create_export_rejects_unsupported_backend():
    routes = _build_routes()

    response = routes.create_export({"job_id": "job-1", "run_id": "run-1", "backend": "onnx"})

    assert response["ok"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"


def test_create_export_requires_backend_field():
    routes = _build_routes()

    response = routes.create_export({"job_id": "job-1", "run_id": "run-1"})

    assert response["ok"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"


def test_export_status_polling_structure_is_stable():
    routes = _build_routes(executor=lambda _payload: {"exit_code": 0, "stdout": "ok", "stderr": ""})

    created = routes.create_export({"job_id": "job-1", "run_id": "run-1", "backend": "tensorrt"})
    polled = routes.get_export_status(created["data"]["export_id"])

    assert created["ok"] is True
    assert polled["ok"] is True
    assert set(polled["data"]) == {"export_id", "job_id", "run_id", "backend", "status", "result"}


def test_export_failure_maps_export_failed():
    routes = _build_routes(executor=lambda _payload: {"exit_code": 9, "stdout": "", "stderr": "boom"})

    created = routes.create_export({"job_id": "job-1", "run_id": "run-1", "backend": "tensorrt"})
    polled = routes.get_export_status(created["data"]["export_id"])

    assert polled["ok"] is True
    assert polled["data"]["status"] == "failed"
    assert polled["data"]["result"]["error_code"] == "EXPORT_FAILED"


def test_get_deploy_benchmark_contract_shape():
    routes = _build_routes(executor=lambda _payload: {"exit_code": 0, "stdout": "ok", "stderr": ""})
    created = routes.create_export({"job_id": "job-1", "run_id": "run-1", "backend": "tensorrt"})

    response = routes.get_deploy_benchmark(created["data"]["export_id"])

    assert response["ok"] is True
    assert set(response["data"]["benchmark"]) == {"throughput_fps", "latency_p95_ms", "memory_mb", "unit"}
