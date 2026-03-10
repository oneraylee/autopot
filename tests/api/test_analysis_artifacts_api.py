from repositories.artifact_repository import ArtifactRepository
from repositories.dataset_repository import DatasetRepository
from repositories.job_repository import JobRepository
from services.job_service import JobService


def _build_routes():
    from api.analysis_routes import AnalysisRoutes

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

    return AnalysisRoutes(job_repository=job_repo, artifact_repository=artifact_repo)


def test_eval_report_contract_and_path_format():
    routes = _build_routes()
    routes.register_artifact_payload(
        job_id="job-1",
        run_id="run-1",
        artifact_type="eval",
        locator="outputs/run-1/eval/report.json",
        payload={
            "overall": {"business_kpi": 0.8, "kpi_components": []},
            "by_scene": [{"scene": "day", "kpi": 0.81}],
        },
    )

    response = routes.get_eval_report("job-1", run_id="run-1")

    assert response["ok"] is True
    assert response["data"]["locator"].startswith("outputs/")
    assert response["data"]["locator_type"] == "relative_path"


def test_evidence_pack_stage_not_ready_is_rejected():
    routes = _build_routes()

    response = routes.get_evidence_pack("job-1", run_id="run-1")

    assert response["ok"] is False
    assert response["error"]["code"] in {"DATA_INVALID", "NOT_FOUND"}


def test_next_experiments_invalid_payload_is_rejected():
    routes = _build_routes()
    routes.register_artifact_payload(
        job_id="job-1",
        run_id="run-1",
        artifact_type="llm",
        locator="outputs/run-1/llm/next.json",
        payload={"experiments": []},
    )

    response = routes.get_next_experiments("job-1", run_id="run-1")

    assert response["ok"] is False
    assert response["error"]["code"] == "DATA_INVALID"


def test_analysis_report_missing_returns_not_found():
    routes = _build_routes()

    response = routes.get_analysis_report("job-1", run_id="run-1")

    assert response["ok"] is False
    assert response["error"]["code"] == "NOT_FOUND"
