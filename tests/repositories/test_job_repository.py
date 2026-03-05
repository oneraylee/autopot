import pytest


def test_create_job_requires_mandatory_fields():
    from repositories.errors import RepositoryError
    from repositories.job_repository import JobRepository

    repository = JobRepository()

    with pytest.raises(RepositoryError) as error:
        repository.create_job(job_id="", task_type="training", dataset_version_id="ds-1:v1")

    assert error.value.code == "VALIDATION_ERROR"


def test_valid_state_transition_sequence():
    from repositories.job_repository import JobRepository

    repository = JobRepository()
    repository.create_job(job_id="job-1", task_type="training", dataset_version_id="ds-1:v1")
    for to_status in [
        "queued",
        "running",
        "succeeded",
        "evaluating",
        "eval_succeeded",
        "evidence_ready",
        "llm_analyzing",
        "llm_done",
    ]:
        repository.transition_status("job-1", to_status=to_status)

    snapshot = repository.get_job("job-1")
    assert snapshot["status"] == "llm_done"


def test_invalid_state_transition_blocked():
    from repositories.errors import RepositoryError
    from repositories.job_repository import JobRepository

    repository = JobRepository()
    repository.create_job(job_id="job-1", task_type="training", dataset_version_id="ds-1:v1")

    with pytest.raises(RepositoryError) as error:
        repository.transition_status("job-1", to_status="running")

    assert error.value.code == "INVALID_TRANSITION"


def test_terminal_state_rejects_further_transition():
    from repositories.errors import RepositoryError
    from repositories.job_repository import JobRepository

    repository = JobRepository()
    repository.create_job(job_id="job-1", task_type="training", dataset_version_id="ds-1:v1")
    repository.transition_status("job-1", to_status="queued")
    repository.transition_status("job-1", to_status="running")
    repository.transition_status("job-1", to_status="failed")

    with pytest.raises(RepositoryError) as error:
        repository.transition_status("job-1", to_status="queued")

    assert error.value.code == "INVALID_TRANSITION"


def test_event_chain_and_resource_records_are_traceable():
    from repositories.job_repository import JobRepository

    repository = JobRepository()
    repository.create_job(job_id="job-1", task_type="training", dataset_version_id="ds-1:v1")
    repository.transition_status("job-1", to_status="queued")
    repository.transition_status("job-1", to_status="running")
    repository.record_resource_usage("job-1", cpu_cores=8, memory_mb=16384, gpu_devices=["0", "1"])
    repository.record_resource_usage("job-1", cpu_cores=10, memory_mb=20000, gpu_devices=["0", "1"])

    events = repository.list_events("job-1")
    resources = repository.get_resource_records("job-1")

    assert [event["to_status"] for event in events] == ["created", "queued", "running"]
    assert len(resources) == 2
    assert resources[0]["sequence"] < resources[1]["sequence"]
