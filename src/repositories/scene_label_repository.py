from collections import Counter
from copy import deepcopy

from .errors import RepositoryError, require_non_empty


class SceneLabelRepository:
    _ENUMS = {
        "time_of_day": {"day", "night", "unknown"},
        "weather": {"sunny", "rain", "fog", "snow", "other", "unknown"},
        "environment": {"indoor", "outdoor", "unknown"},
    }

    def __init__(self) -> None:
        self._store: dict[str, dict[str, dict]] = {}

    def validate_scene_label(self, label: dict) -> None:
        if not isinstance(label, dict):
            raise RepositoryError("VALIDATION_ERROR", "label must be dict")
        for field_name, candidates in self._ENUMS.items():
            value = label.get(field_name)
            if value not in candidates:
                raise RepositoryError("VALIDATION_ERROR", f"invalid {field_name}")
        if label.get("weather") == "other":
            weather_other_text = label.get("weather_other_text", "")
            require_non_empty(weather_other_text, field_name="weather_other_text")

    def create_or_update_label(self, *, dataset_version_id: str, image_id: str, label: dict) -> dict:
        require_non_empty(dataset_version_id, field_name="dataset_version_id")
        require_non_empty(image_id, field_name="image_id")
        self.validate_scene_label(label)

        dataset_labels = self._store.setdefault(dataset_version_id, {})
        record = {
            "dataset_version_id": dataset_version_id,
            "image_id": image_id,
            "time_of_day": label["time_of_day"],
            "weather": label["weather"],
            "environment": label["environment"],
            "weather_other_text": label.get("weather_other_text"),
        }
        dataset_labels[image_id] = record
        return deepcopy(record)

    def batch_upsert_labels(self, *, dataset_version_id: str, labels: list[dict]) -> list[dict]:
        require_non_empty(dataset_version_id, field_name="dataset_version_id")
        if not isinstance(labels, list):
            raise RepositoryError("VALIDATION_ERROR", "labels must be list")

        prepared_records: list[dict] = []
        for item in labels:
            image_id = item.get("image_id", "")
            require_non_empty(image_id, field_name="image_id")
            self.validate_scene_label(item)
            prepared_records.append(
                {
                    "dataset_version_id": dataset_version_id,
                    "image_id": image_id,
                    "time_of_day": item["time_of_day"],
                    "weather": item["weather"],
                    "environment": item["environment"],
                    "weather_other_text": item.get("weather_other_text"),
                }
            )

        dataset_labels = self._store.setdefault(dataset_version_id, {})
        for record in prepared_records:
            dataset_labels[record["image_id"]] = record
        return deepcopy(prepared_records)

    def stats_by_dimension(self, *, dataset_version_id: str, dimension: str, include_unknown: bool = False) -> list[dict]:
        if dimension not in self._ENUMS:
            raise RepositoryError("VALIDATION_ERROR", "invalid dimension")

        labels = list(self._store.get(dataset_version_id, {}).values())
        values = [item[dimension] for item in labels if include_unknown or item[dimension] != "unknown"]
        return self._format_counter(Counter(values))

    def stats_by_combinations(self, *, dataset_version_id: str, dimensions: list[str], include_unknown: bool = False) -> list[dict]:
        if not isinstance(dimensions, list) or not dimensions:
            raise RepositoryError("VALIDATION_ERROR", "dimensions must be non-empty list")
        for dimension in dimensions:
            if dimension not in self._ENUMS:
                raise RepositoryError("VALIDATION_ERROR", "invalid dimension")

        labels = list(self._store.get(dataset_version_id, {}).values())
        counter = Counter()
        for item in labels:
            if not include_unknown and any(item[dimension] == "unknown" for dimension in dimensions):
                continue
            counter["+".join(item[dimension] for dimension in dimensions)] += 1
        return self._format_counter(counter)

    @staticmethod
    def _format_counter(counter: Counter) -> list[dict]:
        total = sum(counter.values())
        if total == 0:
            return []
        output = []
        for key in sorted(counter):
            count = counter[key]
            output.append(
                {
                    "dimension_key": key,
                    "count": count,
                    "ratio": count / total,
                }
            )
        return output
