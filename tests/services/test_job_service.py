import pytest


def _build_frozen_dataset(dataset_repository):
    dataset_repository.create_dataset(dataset_id="ds-1", project_id="proj-1", name="raw")
    dataset_repository.create_dataset_version(dataset_id="ds-1", version=1, manifest_uri="s3://bucket/v1.json")
    dataset_repository.freeze_version(dataset_id="ds-1", version=1)


def test_create_and_queue_requires_frozen_dataset_version():
    from repositories.dataset_repository import DatasetRepository
    from repositories.errors import RepositoryError
    from repositories.job_repository import JobRepository
    from services.job_service import JobService

    dataset_repository = DatasetRepository()
    dataset_repository.create_dataset(dataset_id="ds-1", project_id="proj-1", name="raw")
    dataset_repository.create_dataset_version(dataset_id="ds-1", version=1, manifest_uri="s3://bucket/v1.json")

    service = JobService(job_repository=JobRepository(), dataset_repository=dataset_repository)

    with pytest.raises(RepositoryError) as error:
        service.create_and_queue_job(job_id="job-1", task_type="training", dataset_version_id="ds-1:v1")

    assert error.value.code == "DATA_INVALID"


def test_valid_state_transition_with_lock_and_release():
    from repositories.dataset_repository import DatasetRepository
    from repositories.job_repository import JobRepository
    from services.job_service import JobService

    dataset_repository = DatasetRepository()
    _build_frozen_dataset(dataset_repository)
    service = JobService(job_repository=JobRepository(), dataset_repository=dataset_repository)

    service.create_and_queue_job(job_id="job-1", task_type="training", dataset_version_id="ds-1:v1")
    service.start_job(job_id="job-1", gpu_id="0")
    service.finish_job(job_id="job-1")
    snapshot = service.get_job("job-1")

    assert snapshot["status"] == "succeeded"
    assert service.current_locks() == {}


def test_invalid_state_transition_blocked():
    from repositories.dataset_repository import DatasetRepository
    from repositories.errors import RepositoryError
    from repositories.job_repository import JobRepository
    from services.job_service import JobService

    dataset_repository = DatasetRepository()
    _build_frozen_dataset(dataset_repository)
    service = JobService(job_repository=JobRepository(), dataset_repository=dataset_repository)
    service.create_and_queue_job(job_id="job-1", task_type="training", dataset_version_id="ds-1:v1")

    with pytest.raises(RepositoryError) as error:
        service.finish_job(job_id="job-1")

    assert error.value.code == "INVALID_TRANSITION"


def test_gpu_lock_conflict_is_rejected():
    from repositories.dataset_repository import DatasetRepository
    from repositories.errors import RepositoryError
    from repositories.job_repository import JobRepository
    from services.job_service import JobService

    dataset_repository = DatasetRepository()
    _build_frozen_dataset(dataset_repository)
    service = JobService(job_repository=JobRepository(), dataset_repository=dataset_repository)

    service.create_and_queue_job(job_id="job-1", task_type="training", dataset_version_id="ds-1:v1")
    service.create_and_queue_job(job_id="job-2", task_type="training", dataset_version_id="ds-1:v1")
    service.start_job(job_id="job-1", gpu_id="0")

    with pytest.raises(RepositoryError) as error:
        service.start_job(job_id="job-2", gpu_id="0")

    assert error.value.code == "RESOURCE_LOCKED"


def test_resource_release_is_idempotent_on_failure():
    from repositories.dataset_repository import DatasetRepository
    from repositories.job_repository import JobRepository
    from services.job_service import JobService

    dataset_repository = DatasetRepository()
    _build_frozen_dataset(dataset_repository)
    service = JobService(job_repository=JobRepository(), dataset_repository=dataset_repository)

    service.create_and_queue_job(job_id="job-1", task_type="training", dataset_version_id="ds-1:v1")
    service.start_job(job_id="job-1", gpu_id="1")
    service.fail_job(job_id="job-1", reason="nan")
    service.release_job_resources(job_id="job-1")

    assert service.current_locks() == {}
