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
    assert {"export_id", "job_id", "run_id", "backend", "status", "created_at", "result"}.issubset(set(polled["data"]))


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
    assert {"throughput_fps", "latency_p95_ms", "latency_ms", "memory_mb", "unit"}.issubset(set(response["data"]["benchmark"]))


# ── Phase 1 Step 3: 导出状态与 benchmark 契约对齐门禁 ──


def test_export_status_shape_matches_frontend_contract():
    routes = _build_routes(executor=lambda _payload: {"exit_code": 0, "stdout": "ok", "stderr": ""})
    created = routes.create_export({"job_id": "job-1", "run_id": "run-1", "backend": "tensorrt"})

    polled = routes.get_export_status(created["data"]["export_id"])

    assert polled["ok"] is True
    data = polled["data"]
    required = {"export_id", "job_id", "run_id", "backend", "status", "created_at"}
    assert required.issubset(set(data.keys())), f"Missing fields: {required - set(data.keys())}"


def test_export_status_contains_created_at():
    routes = _build_routes(executor=lambda _payload: {"exit_code": 0, "stdout": "ok", "stderr": ""})
    created = routes.create_export({"job_id": "job-1", "run_id": "run-1", "backend": "tensorrt"})

    polled = routes.get_export_status(created["data"]["export_id"])

    assert polled["ok"] is True
    assert isinstance(polled["data"]["created_at"], str)
    assert len(polled["data"]["created_at"]) > 0


def test_deploy_benchmark_shape_matches_frontend_contract():
    routes = _build_routes(executor=lambda _payload: {"exit_code": 0, "stdout": "ok", "stderr": ""})
    created = routes.create_export({"job_id": "job-1", "run_id": "run-1", "backend": "tensorrt"})

    response = routes.get_deploy_benchmark(created["data"]["export_id"])

    assert response["ok"] is True
    benchmark = response["data"]["benchmark"]
    # Frontend expects: latency_ms, throughput_fps, memory_mb (no unit)
    frontend_required = {"latency_ms", "throughput_fps", "memory_mb"}
    assert frontend_required.issubset(set(benchmark.keys()))


def test_export_failure_preserves_diagnostic_result():
    routes = _build_routes(executor=lambda _payload: {"exit_code": 1, "stdout": "partial", "stderr": "OOM"})
    created = routes.create_export({"job_id": "job-1", "run_id": "run-1", "backend": "tensorrt"})

    polled = routes.get_export_status(created["data"]["export_id"])

    assert polled["ok"] is True
    assert polled["data"]["status"] == "failed"
    result = polled["data"].get("result", {})
    assert "stderr" in result or "diagnostic" in result


def test_export_http_flow_returns_contract_aligned_payloads():
    from fastapi.testclient import TestClient
    from web.app import create_app

    client = TestClient(create_app())
    container = client.app.state.container
    container.project_repository.create_project(project_id="proj-1", name="demo", owner="owner")
    container.dataset_repository.create_dataset(dataset_id="ds-1", project_id="proj-1", name="raw")
    client.post("/datasets/ds-1/versions/import", json={"version": 1, "manifest_uri": "s3://bucket/v1.json"})
    client.post("/datasets/ds-1/versions/1/freeze")
    client.post("/jobs", json={"job_id": "job-1", "task_type": "training", "dataset_version_id": "ds-1:v1", "resources": {"gpu_count": 1}})
    client.post("/jobs/job-1/start", json={"gpu_id": "0"})
    container.job_service.finish_job(job_id="job-1")

    create_resp = client.post("/exports", json={"job_id": "job-1", "run_id": "run-1", "backend": "tensorrt"})
    assert create_resp.status_code == 200
    export_id = create_resp.json()["data"]["export_id"]

    status_resp = client.get(f"/exports/{export_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()["data"]
    assert "created_at" in status_data

    bench_resp = client.get(f"/exports/{export_id}/deploy-benchmark")
    assert bench_resp.status_code == 200
    bench_data = bench_resp.json()["data"]["benchmark"]
    assert "latency_ms" in bench_data
