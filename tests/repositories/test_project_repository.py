import pytest


def test_project_create_and_get_success():
    from repositories.project_repository import ProjectRepository

    repository = ProjectRepository()
    created = repository.create_project(project_id="proj-1", name="Autonomous Driving", owner="alice")
    loaded = repository.get_project("proj-1")

    assert created["project_id"] == "proj-1"
    assert loaded == created


def test_project_update_keeps_identity():
    from repositories.project_repository import ProjectRepository

    repository = ProjectRepository()
    repository.create_project(project_id="proj-1", name="P1", owner="alice")
    updated = repository.update_project("proj-1", name="P1-Renamed")

    assert updated["project_id"] == "proj-1"
    assert updated["name"] == "P1-Renamed"
    assert updated["owner"] == "alice"


def test_kpi_config_multi_version_read():
    from repositories.project_repository import ProjectRepository

    repository = ProjectRepository()
    repository.create_project(project_id="proj-1", name="P1", owner="alice")
    repository.save_kpi_config("proj-1", {"primary_kpi": "accuracy", "threshold": 0.8}, version=1)
    repository.save_kpi_config("proj-1", {"primary_kpi": "recall", "threshold": 0.7}, version=2)

    v1 = repository.get_kpi_config("proj-1", version=1)
    v2 = repository.get_kpi_config("proj-1", version=2)

    assert v1["version"] == 1
    assert v1["primary_kpi"] == "accuracy"
    assert v2["version"] == 2
    assert v2["primary_kpi"] == "recall"


def test_kpi_config_default_version_fallback():
    from repositories.project_repository import ProjectRepository

    repository = ProjectRepository()
    repository.create_project(project_id="proj-1", name="P1", owner="alice")
    repository.save_kpi_config("proj-1", {"primary_kpi": "accuracy", "threshold": 0.8}, version=1)
    repository.save_kpi_config("proj-1", {"primary_kpi": "f1", "threshold": 0.75}, version=3)

    latest = repository.get_kpi_config("proj-1")
    assert latest["version"] == 3
    assert latest["primary_kpi"] == "f1"


def test_project_not_found_error_semantics():
    from repositories.errors import RepositoryError
    from repositories.project_repository import ProjectRepository

    repository = ProjectRepository()

    with pytest.raises(RepositoryError) as error:
        repository.get_project("missing")

    assert error.value.code == "NOT_FOUND"
    assert "project" in error.value.message.lower()


def test_project_repository_query_model_is_stable():
    from repositories.project_repository import ProjectRepository

    repository = ProjectRepository()
    created = repository.create_project(project_id="proj-1", name="P1", owner="alice")

    assert set(created.keys()) == {"project_id", "name", "owner", "created_at", "updated_at"}
