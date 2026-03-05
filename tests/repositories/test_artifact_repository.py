import pytest


def test_register_and_list_artifacts_by_job_and_run():
    from repositories.artifact_repository import ArtifactRepository

    repository = ArtifactRepository()
    repository.register_artifact(
        job_id="job-1",
        run_id="run-1",
        artifact_type="weights",
        locator="outputs/run-1/weights/best.pt",
    )
    repository.register_artifact(
        job_id="job-1",
        run_id="run-1",
        artifact_type="eval",
        locator="outputs/run-1/eval/eval_report.json",
    )

    artifacts = repository.list_artifacts(job_id="job-1", run_id="run-1")
    assert len(artifacts) == 2
    assert {item["artifact_type"] for item in artifacts} == {"weights", "eval"}


def test_illegal_path_rejected():
    from repositories.artifact_repository import ArtifactRepository
    from repositories.errors import RepositoryError

    repository = ArtifactRepository()

    with pytest.raises(RepositoryError) as error:
        repository.register_artifact(
            job_id="job-1",
            run_id="run-1",
            artifact_type="weights",
            locator="../escape/best.pt",
        )

    assert error.value.code == "VALIDATION_ERROR"


def test_support_relative_path_or_object_id_lookup():
    from repositories.artifact_repository import ArtifactRepository

    repository = ArtifactRepository()
    repository.register_artifact(
        job_id="job-1",
        run_id="run-1",
        artifact_type="evidence",
        locator="s3://bucket/evidence/job-1/run-1/evidence.json",
    )
    repository.register_artifact(
        job_id="job-1",
        run_id="run-1",
        artifact_type="llm",
        locator="outputs/run-1/llm/analysis.md",
    )

    artifacts = repository.list_artifacts(job_id="job-1")
    locator_types = {item["locator_type"] for item in artifacts}

    assert locator_types == {"object_id", "relative_path"}


def test_artifact_output_contract_stable_fields():
    from repositories.artifact_repository import ArtifactRepository

    repository = ArtifactRepository()
    created = repository.register_artifact(
        job_id="job-1",
        run_id="run-1",
        artifact_type="export",
        locator="outputs/run-1/export/report.zip",
    )

    assert set(created.keys()) == {
        "artifact_id",
        "job_id",
        "run_id",
        "artifact_type",
        "locator",
        "locator_type",
        "created_at",
    }
