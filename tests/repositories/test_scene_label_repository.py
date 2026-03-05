import pytest


def test_label_write_rejects_invalid_enum():
    from repositories.errors import RepositoryError
    from repositories.scene_label_repository import SceneLabelRepository

    repository = SceneLabelRepository()

    with pytest.raises(RepositoryError) as error:
        repository.create_or_update_label(
            dataset_version_id="ds-1:v1",
            image_id="img-1",
            label={"time_of_day": "dawn", "weather": "sunny", "environment": "outdoor"},
        )

    assert error.value.code == "VALIDATION_ERROR"


def test_weather_other_requires_text():
    from repositories.errors import RepositoryError
    from repositories.scene_label_repository import SceneLabelRepository

    repository = SceneLabelRepository()

    with pytest.raises(RepositoryError) as error:
        repository.create_or_update_label(
            dataset_version_id="ds-1:v1",
            image_id="img-1",
            label={"time_of_day": "night", "weather": "other", "environment": "outdoor"},
        )

    assert error.value.code == "VALIDATION_ERROR"


def test_label_upsert_is_idempotent():
    from repositories.scene_label_repository import SceneLabelRepository

    repository = SceneLabelRepository()
    repository.create_or_update_label(
        dataset_version_id="ds-1:v1",
        image_id="img-1",
        label={"time_of_day": "day", "weather": "sunny", "environment": "outdoor"},
    )
    repository.create_or_update_label(
        dataset_version_id="ds-1:v1",
        image_id="img-1",
        label={"time_of_day": "night", "weather": "rain", "environment": "outdoor"},
    )
    result = repository.stats_by_dimension(dataset_version_id="ds-1:v1", dimension="weather")

    assert sum(item["count"] for item in result) == 1
    assert {item["dimension_key"] for item in result} == {"rain"}


def test_batch_write_transaction_consistency():
    from repositories.errors import RepositoryError
    from repositories.scene_label_repository import SceneLabelRepository

    repository = SceneLabelRepository()

    with pytest.raises(RepositoryError):
        repository.batch_upsert_labels(
            dataset_version_id="ds-1:v1",
            labels=[
                {"image_id": "img-1", "time_of_day": "day", "weather": "sunny", "environment": "outdoor"},
                {"image_id": "img-2", "time_of_day": "night", "weather": "storm", "environment": "outdoor"},
            ],
        )

    assert repository.stats_by_dimension(dataset_version_id="ds-1:v1", dimension="weather") == []


def test_stats_by_dimension_and_combination_correctness():
    from repositories.scene_label_repository import SceneLabelRepository

    repository = SceneLabelRepository()
    repository.batch_upsert_labels(
        dataset_version_id="ds-1:v1",
        labels=[
            {"image_id": "img-1", "time_of_day": "day", "weather": "sunny", "environment": "outdoor"},
            {"image_id": "img-2", "time_of_day": "night", "weather": "rain", "environment": "indoor"},
            {"image_id": "img-3", "time_of_day": "night", "weather": "rain", "environment": "outdoor"},
        ],
    )

    by_weather = repository.stats_by_dimension(dataset_version_id="ds-1:v1", dimension="weather")
    combo = repository.stats_by_combinations(dataset_version_id="ds-1:v1", dimensions=["time_of_day", "weather"])

    weather_map = {item["dimension_key"]: item for item in by_weather}
    combo_map = {item["dimension_key"]: item for item in combo}

    assert weather_map["rain"]["count"] == 2
    assert weather_map["rain"]["ratio"] == pytest.approx(2 / 3)
    assert combo_map["night+rain"]["count"] == 2


def test_aggregation_output_contract_stable_fields():
    from repositories.scene_label_repository import SceneLabelRepository

    repository = SceneLabelRepository()
    repository.create_or_update_label(
        dataset_version_id="ds-1:v1",
        image_id="img-1",
        label={"time_of_day": "day", "weather": "sunny", "environment": "outdoor"},
    )

    output = repository.stats_by_dimension(dataset_version_id="ds-1:v1", dimension="weather")
    assert set(output[0].keys()) == {"dimension_key", "count", "ratio"}
