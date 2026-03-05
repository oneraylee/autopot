from copy import deepcopy
from datetime import UTC, datetime

from .errors import RepositoryError, require_non_empty


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class ProjectRepository:
    def __init__(self) -> None:
        self._projects: dict[str, dict] = {}
        self._kpi_versions: dict[str, dict[int, dict]] = {}

    def create_project(self, *, project_id: str, name: str, owner: str) -> dict:
        require_non_empty(project_id, field_name="project_id")
        require_non_empty(name, field_name="name")
        require_non_empty(owner, field_name="owner")
        if project_id in self._projects:
            raise RepositoryError("CONFLICT", "project already exists")
        timestamp = _now()
        project = {
            "project_id": project_id,
            "name": name,
            "owner": owner,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        self._projects[project_id] = project
        return deepcopy(project)

    def get_project(self, project_id: str) -> dict:
        project = self._projects.get(project_id)
        if project is None:
            raise RepositoryError("NOT_FOUND", "project not found")
        return deepcopy(project)

    def update_project(self, project_id: str, **updates: str) -> dict:
        project = self._projects.get(project_id)
        if project is None:
            raise RepositoryError("NOT_FOUND", "project not found")
        for field_name in ("name", "owner"):
            value = updates.get(field_name)
            if value is not None:
                require_non_empty(value, field_name=field_name)
                project[field_name] = value
        project["updated_at"] = _now()
        return deepcopy(project)

    def save_kpi_config(self, project_id: str, config: dict, *, version: int) -> dict:
        self.get_project(project_id)
        if not isinstance(version, int) or version <= 0:
            raise RepositoryError("VALIDATION_ERROR", "version must be positive integer")
        if not isinstance(config, dict):
            raise RepositoryError("VALIDATION_ERROR", "config must be dict")
        primary_kpi = config.get("primary_kpi")
        threshold = config.get("threshold")
        require_non_empty(primary_kpi, field_name="primary_kpi")
        if not isinstance(threshold, (int, float)):
            raise RepositoryError("VALIDATION_ERROR", "threshold must be numeric")

        project_versions = self._kpi_versions.setdefault(project_id, {})
        record = {
            "project_id": project_id,
            "version": version,
            "primary_kpi": primary_kpi,
            "threshold": float(threshold),
            "created_at": _now(),
        }
        project_versions[version] = record
        return deepcopy(record)

    def get_kpi_config(self, project_id: str, version: int | None = None) -> dict:
        self.get_project(project_id)
        project_versions = self._kpi_versions.get(project_id, {})
        if not project_versions:
            raise RepositoryError("NOT_FOUND", "kpi config not found")

        effective_version = version if version is not None else max(project_versions)
        record = project_versions.get(effective_version)
        if record is None:
            raise RepositoryError("NOT_FOUND", "kpi config not found")
        return deepcopy(record)
