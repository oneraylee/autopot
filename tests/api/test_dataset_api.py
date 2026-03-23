from repositories.dataset_repository import DatasetRepository
from repositories.scene_label_repository import SceneLabelRepository


def _build_routes():
    from api.dataset_routes import DatasetRoutes

    dataset_repo = DatasetRepository()
    scene_repo = SceneLabelRepository()
    dataset_repo.create_dataset(dataset_id="ds-1", project_id="proj-1", name="raw")
    return DatasetRoutes(dataset_repository=dataset_repo, scene_label_repository=scene_repo)


def test_import_dataset_success_returns_version_identifier():
    routes = _build_routes()

    response = routes.import_dataset_version("ds-1", {"version": 1, "manifest_uri": "s3://bucket/v1.json"})

    assert response["ok"] is True
    assert response["data"]["dataset_version_id"] == "ds-1:v1"


def test_freeze_dataset_duplicate_freeze_is_diagnosable():
    routes = _build_routes()
    routes.import_dataset_version("ds-1", {"version": 1, "manifest_uri": "s3://bucket/v1.json"})

    first = routes.freeze_dataset_version("ds-1", 1)
    second = routes.freeze_dataset_version("ds-1", 1)

    assert first["ok"] is True
    assert second["ok"] is False
    assert second["error"]["code"] == "CONFLICT"


def test_upsert_scene_labels_weather_other_requires_text():
    routes = _build_routes()
    routes.import_dataset_version("ds-1", {"version": 1, "manifest_uri": "s3://bucket/v1.json"})

    response = routes.upsert_scene_labels(
        "ds-1:v1",
        [
            {
                "image_id": "img-1",
                "time_of_day": "day",
                "weather": "other",
                "environment": "outdoor",
            }
        ],
    )

    assert response["ok"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"


def test_scene_coverage_statistics_shape_is_stable():
    routes = _build_routes()
    routes.import_dataset_version("ds-1", {"version": 1, "manifest_uri": "s3://bucket/v1.json"})

    routes.upsert_scene_labels(
        "ds-1:v1",
        [
            {
                "image_id": "img-1",
                "time_of_day": "day",
                "weather": "sunny",
                "environment": "outdoor",
            },
            {
                "image_id": "img-2",
                "time_of_day": "night",
                "weather": "rain",
                "environment": "outdoor",
            },
        ],
    )

    response = routes.get_scene_coverage("ds-1:v1", ["time_of_day", "weather"])

    assert response["ok"] is True
    assert response["data"]["items"][0]["dimension_key"]
    assert set(response["data"]) == {"dataset_version_id", "dimensions", "items"}


def test_empty_scene_coverage_returns_empty_collection():
    routes = _build_routes()

    response = routes.get_scene_coverage("ds-1:v1", ["weather"])

    assert response["ok"] is True
    assert response["data"]["items"] == []


# ── Phase 1 Step 1: 数据集列表查询接口测试基线 ──


def test_list_datasets_returns_empty_collection_when_no_datasets():
    from api.dataset_routes import DatasetRoutes

    dataset_repo = DatasetRepository()
    scene_repo = SceneLabelRepository()
    routes = DatasetRoutes(dataset_repository=dataset_repo, scene_label_repository=scene_repo)

    response = routes.list_datasets()

    assert response["ok"] is True
    assert response["data"]["items"] == []


def test_list_datasets_returns_latest_version_projection():
    routes = _build_routes()
    routes.import_dataset_version("ds-1", {"version": 1, "manifest_uri": "s3://bucket/v1.json"})
    routes.import_dataset_version("ds-1", {"version": 2, "manifest_uri": "s3://bucket/v2.json"})

    response = routes.list_datasets()

    assert response["ok"] is True
    items = response["data"]["items"]
    assert len(items) == 1
    item = items[0]
    required_fields = {"dataset_id", "name", "latest_version", "created_at"}
    assert required_fields.issubset(set(item.keys()))
    assert item["latest_version"] == 2
