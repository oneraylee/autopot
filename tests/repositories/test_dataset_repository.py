import pytest


def test_dataset_and_version_create_success():
    from repositories.dataset_repository import DatasetRepository

    repository = DatasetRepository()
    repository.create_dataset(dataset_id="ds-1", project_id="proj-1", name="raw-data")
    version = repository.create_dataset_version(
        dataset_id="ds-1",
        version=1,
        manifest_uri="s3://bucket/datasets/ds-1/v1/manifest.json",
    )

    assert version["dataset_version_id"] == "ds-1:v1"
    assert version["frozen"] is False


def test_duplicate_version_conflict():
    from repositories.dataset_repository import DatasetRepository
    from repositories.errors import RepositoryError

    repository = DatasetRepository()
    repository.create_dataset(dataset_id="ds-1", project_id="proj-1", name="raw-data")
    repository.create_dataset_version(dataset_id="ds-1", version=1, manifest_uri="s3://bucket/v1.json")

    with pytest.raises(RepositoryError) as error:
        repository.create_dataset_version(dataset_id="ds-1", version=1, manifest_uri="s3://bucket/v1b.json")

    assert error.value.code == "VERSION_CONFLICT"


def test_freeze_blocks_destructive_update():
    from repositories.dataset_repository import DatasetRepository
    from repositories.errors import RepositoryError

    repository = DatasetRepository()
    repository.create_dataset(dataset_id="ds-1", project_id="proj-1", name="raw-data")
    repository.create_dataset_version(dataset_id="ds-1", version=1, manifest_uri="s3://bucket/v1.json")
    repository.freeze_version(dataset_id="ds-1", version=1)

    with pytest.raises(RepositoryError) as error:
        repository.update_dataset_version(
            dataset_id="ds-1",
            version=1,
            manifest_uri="s3://bucket/v1-new.json",
        )

    assert error.value.code == "FROZEN_CONFLICT"


def test_frozen_status_can_be_queried():
    from repositories.dataset_repository import DatasetRepository

    repository = DatasetRepository()
    repository.create_dataset(dataset_id="ds-1", project_id="proj-1", name="raw-data")
    repository.create_dataset_version(dataset_id="ds-1", version=1, manifest_uri="s3://bucket/v1.json")
    repository.freeze_version(dataset_id="ds-1", version=1)
    snapshot = repository.get_dataset_version(dataset_id="ds-1", version=1)

    assert snapshot["frozen"] is True


def test_dataset_query_model_is_stable():
    from repositories.dataset_repository import DatasetRepository

    repository = DatasetRepository()
    dataset = repository.create_dataset(dataset_id="ds-1", project_id="proj-1", name="raw-data")

    assert set(dataset.keys()) == {"dataset_id", "project_id", "name", "created_at", "updated_at"}
