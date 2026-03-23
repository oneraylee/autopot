from copy import deepcopy
from datetime import UTC, datetime

from .errors import RepositoryError, require_non_empty


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class DatasetRepository:
    def __init__(self) -> None:
        self._datasets: dict[str, dict] = {}
        self._versions: dict[tuple[str, int], dict] = {}

    def create_dataset(self, *, dataset_id: str, project_id: str, name: str) -> dict:
        require_non_empty(dataset_id, field_name="dataset_id")
        require_non_empty(project_id, field_name="project_id")
        require_non_empty(name, field_name="name")
        if dataset_id in self._datasets:
            raise RepositoryError("CONFLICT", "dataset already exists")
        timestamp = _now()
        dataset = {
            "dataset_id": dataset_id,
            "project_id": project_id,
            "name": name,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        self._datasets[dataset_id] = dataset
        return deepcopy(dataset)

    def create_dataset_version(self, *, dataset_id: str, version: int, manifest_uri: str) -> dict:
        self._get_dataset(dataset_id)
        require_non_empty(manifest_uri, field_name="manifest_uri")
        key = (dataset_id, version)
        if key in self._versions:
            raise RepositoryError("VERSION_CONFLICT", "dataset version already exists")
        record = {
            "dataset_version_id": f"{dataset_id}:v{version}",
            "dataset_id": dataset_id,
            "version": version,
            "manifest_uri": manifest_uri,
            "frozen": False,
            "created_at": _now(),
            "updated_at": _now(),
        }
        self._versions[key] = record
        return deepcopy(record)

    def update_dataset_version(self, *, dataset_id: str, version: int, manifest_uri: str) -> dict:
        record = self._get_version(dataset_id, version)
        if record["frozen"]:
            raise RepositoryError("FROZEN_CONFLICT", "dataset version is frozen")
        require_non_empty(manifest_uri, field_name="manifest_uri")
        record["manifest_uri"] = manifest_uri
        record["updated_at"] = _now()
        return deepcopy(record)

    def freeze_version(self, *, dataset_id: str, version: int) -> dict:
        record = self._get_version(dataset_id, version)
        record["frozen"] = True
        record["updated_at"] = _now()
        return deepcopy(record)

    def get_dataset_version(self, *, dataset_id: str, version: int) -> dict:
        return deepcopy(self._get_version(dataset_id, version))

    def list_datasets(self) -> list[dict]:
        result = []
        for dataset in self._datasets.values():
            versions = [
                v["version"] for k, v in self._versions.items() if k[0] == dataset["dataset_id"]
            ]
            item = deepcopy(dataset)
            item["latest_version"] = max(versions) if versions else None
            result.append(item)
        return sorted(result, key=lambda d: d["created_at"], reverse=True)

    def _get_dataset(self, dataset_id: str) -> dict:
        dataset = self._datasets.get(dataset_id)
        if dataset is None:
            raise RepositoryError("NOT_FOUND", "dataset not found")
        return dataset

    def _get_version(self, dataset_id: str, version: int) -> dict:
        record = self._versions.get((dataset_id, version))
        if record is None:
            raise RepositoryError("NOT_FOUND", "dataset version not found")
        return record
