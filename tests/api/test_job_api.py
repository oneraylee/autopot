from repositories.dataset_repository import DatasetRepository
from repositories.job_repository import JobRepository
from services.job_service import JobService


def _build_routes():
    from api.job_routes import JobRoutes

    dataset_repo = DatasetRepository()
    job_repo = JobRepository()
    dataset_repo.create_dataset(dataset_id="ds-1", project_id="proj-1", name="raw")
    dataset_repo.create_dataset_version(dataset_id="ds-1", version=1, manifest_uri="s3://bucket/v1.json")
    dataset_repo.freeze_version(dataset_id="ds-1", version=1)
    service = JobService(job_repository=job_repo, dataset_repository=dataset_repo)
    return JobRoutes(job_service=service, job_repository=job_repo)


def test_create_job_success_and_initial_state():
    routes = _build_routes()

    response = routes.create_job(
        {
            "job_id": "job-1",
            "task_type": "training",
            "dataset_version_id": "ds-1:v1",
            "resources": {"gpu_count": 1},
        }
    )

    assert response["ok"] is True
    assert response["data"]["status"] == "queued"


def test_create_job_invalid_resource_rejected():
    routes = _build_routes()

    response = routes.create_job(
        {
            "job_id": "job-1",
            "task_type": "training",
            "dataset_version_id": "ds-1:v1",
            "resources": {"gpu_count": 0},
        }
    )

    assert response["ok"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"


def test_get_job_status_success():
    routes = _build_routes()
    routes.create_job(
        {
            "job_id": "job-1",
            "task_type": "training",
            "dataset_version_id": "ds-1:v1",
            "resources": {"gpu_count": 1},
        }
    )

    response = routes.get_job("job-1")

    assert response["ok"] is True
    assert response["data"]["job_id"] == "job-1"


def test_get_job_status_not_found():
    routes = _build_routes()

    response = routes.get_job("job-missing")

    assert response["ok"] is False
    assert response["error"]["code"] == "NOT_FOUND"


def test_job_state_conflict_error_mapping():
    routes = _build_routes()
    routes.create_job(
        {
            "job_id": "job-1",
            "task_type": "training",
            "dataset_version_id": "ds-1:v1",
            "resources": {"gpu_count": 1},
        }
    )
    routes.create_job(
        {
            "job_id": "job-2",
            "task_type": "training",
            "dataset_version_id": "ds-1:v1",
            "resources": {"gpu_count": 1},
        }
    )

    routes.start_job("job-1", gpu_id="0")
    conflict = routes.start_job("job-2", gpu_id="0")

    assert conflict["ok"] is False
    assert conflict["error"]["code"] == "RESOURCE_LOCKED"


def test_logs_pagination_and_empty_metrics_semantics():
    routes = _build_routes()
    routes.create_job(
        {
            "job_id": "job-1",
            "task_type": "training",
            "dataset_version_id": "ds-1:v1",
            "resources": {"gpu_count": 1},
        }
    )
    routes.append_log("job-1", "line-1")
    routes.append_log("job-1", "line-2")

    log_response = routes.get_logs("job-1", page=1, page_size=1)
    metrics_response = routes.get_metrics("job-1", start_ts=100, end_ts=200)

    assert log_response["ok"] is True
    assert len(log_response["data"]["items"]) == 1
    assert metrics_response["ok"] is True
    assert metrics_response["data"]["items"] == []
