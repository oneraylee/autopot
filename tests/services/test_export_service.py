import pytest


def _build_succeeded_job(dataset_repository, job_repository):
    from services.job_service import JobService

    dataset_repository.create_dataset(dataset_id="ds-1", project_id="proj-1", name="raw")
    dataset_repository.create_dataset_version(dataset_id="ds-1", version=1, manifest_uri="s3://bucket/v1.json")
    dataset_repository.freeze_version(dataset_id="ds-1", version=1)

    job_service = JobService(job_repository=job_repository, dataset_repository=dataset_repository)
    job_service.create_and_queue_job(job_id="job-1", task_type="training", dataset_version_id="ds-1:v1")
    job_service.start_job(job_id="job-1", gpu_id="0")
    job_service.finish_job(job_id="job-1")


def test_only_succeeded_or_eval_succeeded_can_export():
    from repositories.artifact_repository import ArtifactRepository
    from repositories.dataset_repository import DatasetRepository
    from repositories.errors import RepositoryError
    from repositories.job_repository import JobRepository
    from services.export_service import ExportService

    dataset_repository = DatasetRepository()
    job_repository = JobRepository()
    dataset_repository.create_dataset(dataset_id="ds-1", project_id="proj-1", name="raw")
    dataset_repository.create_dataset_version(dataset_id="ds-1", version=1, manifest_uri="s3://bucket/v1.json")
    dataset_repository.freeze_version(dataset_id="ds-1", version=1)
    job_repository.create_job(job_id="job-1", task_type="training", dataset_version_id="ds-1:v1")
    service = ExportService(job_repository=job_repository, artifact_repository=ArtifactRepository())

    with pytest.raises(RepositoryError) as error:
        service.create_export_job(job_id="job-1", run_id="run-1", backend="tensorrt")

    assert error.value.code == "DATA_INVALID"


def test_export_success_registers_engine_artifact():
    from repositories.artifact_repository import ArtifactRepository
    from repositories.dataset_repository import DatasetRepository
    from repositories.job_repository import JobRepository
    from services.export_service import ExportService

    dataset_repository = DatasetRepository()
    job_repository = JobRepository()
    artifact_repository = ArtifactRepository()
    _build_succeeded_job(dataset_repository, job_repository)

    service = ExportService(
        job_repository=job_repository,
        artifact_repository=artifact_repository,
        executor=lambda _payload: {
            "exit_code": 0,
            "stdout": "ok",
            "stderr": "",
            "engine_locator": "outputs/run-1/export/model.engine",
        },
    )

    result = service.run_export(job_id="job-1", run_id="run-1", backend="tensorrt")
    artifacts = artifact_repository.list_artifacts(job_id="job-1", run_id="run-1", artifact_type="export")

    assert result["ok"] is True
    assert len(artifacts) == 1
    assert artifacts[0]["locator"].endswith(".engine")


def test_export_failure_maps_export_failed():
    from repositories.artifact_repository import ArtifactRepository
    from repositories.dataset_repository import DatasetRepository
    from repositories.job_repository import JobRepository
    from services.export_service import ExportService

    dataset_repository = DatasetRepository()
    job_repository = JobRepository()
    _build_succeeded_job(dataset_repository, job_repository)

    service = ExportService(
        job_repository=job_repository,
        artifact_repository=ArtifactRepository(),
        executor=lambda _payload: {"exit_code": 9, "stdout": "", "stderr": "export crashed"},
    )
    result = service.run_export(job_id="job-1", run_id="run-1", backend="tensorrt")

    assert result["ok"] is False
    assert result["error_code"] == "EXPORT_FAILED"
    assert "crashed" in result["stderr"]


def test_unknown_backend_rejected_with_clear_error():
    from repositories.artifact_repository import ArtifactRepository
    from repositories.dataset_repository import DatasetRepository
    from repositories.errors import RepositoryError
    from repositories.job_repository import JobRepository
    from services.export_service import ExportService

    dataset_repository = DatasetRepository()
    job_repository = JobRepository()
    _build_succeeded_job(dataset_repository, job_repository)
    service = ExportService(job_repository=job_repository, artifact_repository=ArtifactRepository())

    with pytest.raises(RepositoryError) as error:
        service.create_export_job(job_id="job-1", run_id="run-1", backend="onnx")

    assert error.value.code == "VALIDATION_ERROR"
    assert "backend" in error.value.message.lower()


def test_build_deploy_benchmark_has_complete_fields_and_units():
    from repositories.artifact_repository import ArtifactRepository
    from repositories.job_repository import JobRepository
    from services.export_service import ExportService

    service = ExportService(job_repository=JobRepository(), artifact_repository=ArtifactRepository())
    benchmark = service.build_deploy_benchmark(throughput_fps=120.5, latency_p95_ms=18.2, memory_mb=2048)

    assert benchmark == {
        "throughput_fps": 120.5,
        "latency_p95_ms": 18.2,
        "memory_mb": 2048,
        "unit": {"throughput_fps": "fps", "latency_p95_ms": "ms", "memory_mb": "MB"},
    }


def test_kpi_merge_applies_latency_constraint_and_weighting():
    from repositories.artifact_repository import ArtifactRepository
    from repositories.job_repository import JobRepository
    from services.export_service import ExportService

    service = ExportService(job_repository=JobRepository(), artifact_repository=ArtifactRepository())
    merged = service.merge_deploy_metrics_to_kpi(
        eval_business_kpi=0.80,
        deploy_benchmark={"throughput_fps": 100.0, "latency_p95_ms": 20.0, "memory_mb": 2000},
        project_kpi_config={
            "weights": {"eval": 0.7, "deploy": 0.3},
            "deploy_constraints": {"latency_p95_ms_max": 30.0},
        },
    )

    assert merged["constraint_passed"] is True
    assert merged["merged_business_kpi"] == pytest.approx(0.86)
