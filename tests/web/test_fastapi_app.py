from fastapi.testclient import TestClient

from web.app import create_app


def _seed_project_and_dataset(client: TestClient) -> None:
    container = client.app.state.container
    container.project_repository.create_project(project_id="proj-1", name="demo", owner="owner")
    container.dataset_repository.create_dataset(dataset_id="ds-1", project_id="proj-1", name="raw")
    client.post("/datasets/ds-1/versions/import", json={"version": 1, "manifest_uri": "s3://bucket/v1.json"})
    client.post("/datasets/ds-1/versions/1/freeze")


def test_health_endpoint():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"ok": True, "data": {"status": "up"}}


def test_project_kpi_config_http_flow():
    client = TestClient(create_app())
    container = client.app.state.container
    container.project_repository.create_project(project_id="proj-1", name="demo", owner="owner")

    put_response = client.put(
        "/projects/proj-1/kpi-config",
        json={
            "primary_kpi": "business_kpi",
            "threshold": 0.8,
            "weights": {"eval": 0.7, "deploy": 0.3},
            "deploy_constraints": [{"metric": "latency_p95_ms", "operator": "<=", "value": 30}],
        },
    )
    get_response = client.get("/projects/proj-1/kpi-config")

    assert put_response.status_code == 200
    assert get_response.status_code == 200
    assert get_response.json()["data"]["project_id"] == "proj-1"


def test_job_and_logs_http_flow():
    client = TestClient(create_app())
    _seed_project_and_dataset(client)

    create_response = client.post(
        "/jobs",
        json={
            "job_id": "job-1",
            "task_type": "training",
            "dataset_version_id": "ds-1:v1",
            "resources": {"gpu_count": 1},
        },
    )
    client.post("/jobs/job-1/logs", json={"message": "line-1"})
    logs_response = client.get("/jobs/job-1/logs", params={"page": 1, "page_size": 10})

    assert create_response.status_code == 200
    assert create_response.json()["data"]["status"] == "queued"
    assert logs_response.status_code == 200
    assert logs_response.json()["data"]["items"][0]["message"] == "line-1"


def test_export_http_flow_and_benchmark_query():
    client = TestClient(create_app())
    _seed_project_and_dataset(client)
    client.post(
        "/jobs",
        json={
            "job_id": "job-1",
            "task_type": "training",
            "dataset_version_id": "ds-1:v1",
            "resources": {"gpu_count": 1},
        },
    )
    client.post("/jobs/job-1/start", json={"gpu_id": "0"})
    container = client.app.state.container
    container.job_service.finish_job(job_id="job-1")

    create_export = client.post("/exports", json={"job_id": "job-1", "run_id": "run-1", "backend": "tensorrt"})
    export_id = create_export.json()["data"]["export_id"]
    benchmark = client.get(f"/exports/{export_id}/deploy-benchmark")

    assert create_export.status_code == 200
    assert benchmark.status_code == 200
    assert set(benchmark.json()["data"]["benchmark"]) == {"throughput_fps", "latency_p95_ms", "memory_mb", "unit"}


def test_proposal_validate_http_endpoint():
    client = TestClient(create_app())

    response = client.post(
        "/proposals/validate",
        json={
            "analysis_report": "ok",
            "next_experiments": {
                "experiments": [
                    {
                        "name": "exp-1",
                        "changes": [{"field": "lr", "from": 0.001, "to": 0.0005}],
                        "expected": "higher kpi",
                        "evidence_refs": ["eval_report.overall.business_kpi"],
                    }
                ]
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["accepted"] == 1
