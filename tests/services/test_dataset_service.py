import pytest


def test_class_distribution_consistent_with_total():
    from services.dataset_service import DatasetService

    service = DatasetService()
    report = service.get_dataset_report(
        [
            {"image_id": "1", "classes": ["car", "person"], "bboxes": [[0, 0, 10, 10]], "scene": {"weather": "sunny"}},
            {"image_id": "2", "classes": ["car"], "bboxes": [[0, 0, 30, 30]], "scene": {"weather": "rain"}},
        ]
    )

    assert report["total_samples"] == 2
    assert sum(report["class_distribution"].values()) == 3


def test_empty_image_ratio_with_mixed_dataset():
    from services.dataset_service import DatasetService

    service = DatasetService()
    report = service.get_dataset_report(
        [
            {"image_id": "1", "classes": [], "bboxes": [], "scene": {"weather": "sunny"}},
            {"image_id": "2", "classes": ["car"], "bboxes": [[0, 0, 20, 20]], "scene": {"weather": "rain"}},
            {"image_id": "3", "classes": [], "bboxes": [], "scene": {"weather": "rain"}},
        ]
    )

    assert report["empty_image_ratio"] == pytest.approx(2 / 3)


def test_bbox_size_distribution_bucketed():
    from services.dataset_service import DatasetService

    service = DatasetService()
    report = service.get_dataset_report(
        [
            {"image_id": "1", "classes": ["car"], "bboxes": [[0, 0, 10, 10]], "scene": {"weather": "sunny"}},
            {"image_id": "2", "classes": ["car"], "bboxes": [[0, 0, 50, 50]], "scene": {"weather": "sunny"}},
            {"image_id": "3", "classes": ["car"], "bboxes": [[0, 0, 120, 120]], "scene": {"weather": "sunny"}},
        ]
    )

    assert report["bbox_size_distribution"] == {"small": 1, "medium": 1, "large": 1}


def test_scene_coverage_single_dimension():
    from services.dataset_service import DatasetService

    service = DatasetService()
    coverage = service.compute_scene_coverage(
        [
            {"scene": {"time_of_day": "day", "weather": "sunny"}},
            {"scene": {"time_of_day": "night", "weather": "rain"}},
            {"scene": {"time_of_day": "night", "weather": "rain"}},
        ],
        dimensions=["weather"],
    )

    result_map = {item["dimension_key"]: item for item in coverage}
    assert result_map["rain"]["count"] == 2
    assert result_map["rain"]["ratio"] == pytest.approx(2 / 3)


def test_scene_coverage_combination_dimension():
    from services.dataset_service import DatasetService

    service = DatasetService()
    coverage = service.compute_scene_coverage(
        [
            {"scene": {"time_of_day": "day", "weather": "sunny"}},
            {"scene": {"time_of_day": "night", "weather": "rain"}},
            {"scene": {"time_of_day": "night", "weather": "rain"}},
        ],
        dimensions=["time_of_day", "weather"],
    )

    result_map = {item["dimension_key"]: item for item in coverage}
    assert result_map["night+rain"]["count"] == 2
