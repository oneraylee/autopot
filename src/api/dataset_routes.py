from typing import Any

from api._response import error, run_with_error_mapping


class DatasetRoutes:
    def __init__(self, *, dataset_repository, scene_label_repository) -> None:
        self._dataset_repository = dataset_repository
        self._scene_label_repository = scene_label_repository

    def import_dataset_version(self, dataset_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        def _import() -> dict[str, Any]:
            return self._dataset_repository.create_dataset_version(
                dataset_id=dataset_id,
                version=int(payload.get("version", 0)),
                manifest_uri=str(payload.get("manifest_uri", "")),
            )

        return run_with_error_mapping(_import)

    def freeze_dataset_version(self, dataset_id: str, version: int) -> dict[str, Any]:
        def _freeze() -> dict[str, Any]:
            current = self._dataset_repository.get_dataset_version(dataset_id=dataset_id, version=version)
            if current.get("frozen") is True:
                return error(code="CONFLICT", message="dataset version already frozen")
            return self._dataset_repository.freeze_version(dataset_id=dataset_id, version=version)

        response = run_with_error_mapping(_freeze)
        if response["ok"] and isinstance(response["data"], dict) and "ok" in response["data"]:
            return response["data"]
        return response

    def upsert_scene_labels(self, dataset_version_id: str, labels: list[dict[str, Any]]) -> dict[str, Any]:
        def _upsert() -> dict[str, Any]:
            records = self._scene_label_repository.batch_upsert_labels(
                dataset_version_id=dataset_version_id,
                labels=labels,
            )
            return {"dataset_version_id": dataset_version_id, "items": records}

        return run_with_error_mapping(_upsert)

    def get_scene_coverage(self, dataset_version_id: str, dimensions: list[str]) -> dict[str, Any]:
        def _stats() -> dict[str, Any]:
            if not isinstance(dimensions, list) or not dimensions:
                raise ValueError("dimensions must be non-empty list")
            if len(dimensions) == 1:
                items = self._scene_label_repository.stats_by_dimension(
                    dataset_version_id=dataset_version_id,
                    dimension=dimensions[0],
                    include_unknown=False,
                )
            else:
                items = self._scene_label_repository.stats_by_combinations(
                    dataset_version_id=dataset_version_id,
                    dimensions=dimensions,
                    include_unknown=False,
                )
            return {
                "dataset_version_id": dataset_version_id,
                "dimensions": dimensions,
                "items": items,
            }

        return run_with_error_mapping(_stats)
