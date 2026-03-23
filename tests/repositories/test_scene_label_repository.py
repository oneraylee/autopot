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


# ---------------------------------------------------------------------------
# Phase 3 Step 2 – 场景覆盖率性能基线门禁
# ---------------------------------------------------------------------------

_LARGE_SAMPLE_SIZE = 10_000

_TIME_OF_DAY_VALUES = ["day", "night"]
_WEATHER_VALUES = ["sunny", "rain", "fog", "snow"]
_ENVIRONMENT_VALUES = ["indoor", "outdoor"]


def _seed_large_sample(repo, dataset_version_id: str = "perf-ds:v1", n: int = _LARGE_SAMPLE_SIZE):
    """Deterministically seed *n* labels cycling through known enum values."""
    labels = []
    for i in range(n):
        labels.append(
            {
                "image_id": f"img-{i}",
                "time_of_day": _TIME_OF_DAY_VALUES[i % len(_TIME_OF_DAY_VALUES)],
                "weather": _WEATHER_VALUES[i % len(_WEATHER_VALUES)],
                "environment": _ENVIRONMENT_VALUES[i % len(_ENVIRONMENT_VALUES)],
            }
        )
    repo.batch_upsert_labels(dataset_version_id=dataset_version_id, labels=labels)
    return labels


def test_scene_coverage_single_dimension_result_stays_correct_under_large_sample():
    """单维度统计在万级样本下结果与手工预期一致。"""
    from repositories.scene_label_repository import SceneLabelRepository

    repo = SceneLabelRepository()
    _seed_large_sample(repo)

    result = repo.stats_by_dimension(dataset_version_id="perf-ds:v1", dimension="weather")
    result_map = {item["dimension_key"]: item["count"] for item in result}

    # 4 weather values cycle evenly → each gets n/4
    expected_each = _LARGE_SAMPLE_SIZE // len(_WEATHER_VALUES)
    for val in _WEATHER_VALUES:
        assert result_map[val] == expected_each, f"weather={val} expected {expected_each}, got {result_map.get(val)}"

    # ratios should sum to 1.0
    total_ratio = sum(item["ratio"] for item in result)
    assert total_ratio == pytest.approx(1.0)


def test_scene_coverage_combination_result_stays_correct_under_large_sample():
    """组合维度统计在万级样本下结果与手工预期一致。"""
    from repositories.scene_label_repository import SceneLabelRepository

    repo = SceneLabelRepository()
    _seed_large_sample(repo)

    result = repo.stats_by_combinations(
        dataset_version_id="perf-ds:v1", dimensions=["time_of_day", "weather"]
    )
    result_map = {item["dimension_key"]: item["count"] for item in result}

    # LCM(2,4) = 4 → cycle period is 4.
    # (day,sunny) at i%2==0 & i%4==0 → i=0,8,16,… → n/4
    # (night,rain) at i%2==1 & i%4==1 → i=1,9,17,… → n/4
    # (day,fog) at i%2==0 & i%4==2 → i=2,10,18,… → n/4
    # (night,snow) at i%2==1 & i%4==3 → i=3,11,19,… → n/4
    expected_combos = {
        "day+sunny": _LARGE_SAMPLE_SIZE // 4,
        "night+rain": _LARGE_SAMPLE_SIZE // 4,
        "day+fog": _LARGE_SAMPLE_SIZE // 4,
        "night+snow": _LARGE_SAMPLE_SIZE // 4,
    }
    assert result_map == expected_combos

    total_ratio = sum(item["ratio"] for item in result)
    assert total_ratio == pytest.approx(1.0)


def test_scene_coverage_benchmark_records_execution_time():
    """统计查询耗时可被观测记录（benchmark 元数据门禁）。"""
    import time

    from repositories.scene_label_repository import SceneLabelRepository

    repo = SceneLabelRepository()
    _seed_large_sample(repo)

    t0 = time.perf_counter()
    repo.stats_by_dimension(dataset_version_id="perf-ds:v1", dimension="weather")
    single_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    repo.stats_by_combinations(
        dataset_version_id="perf-ds:v1", dimensions=["time_of_day", "weather", "environment"]
    )
    combo_ms = (time.perf_counter() - t0) * 1000

    # 仅验证耗时被正确捕获（非负且合理）；具体阈值由下一个测试管控
    assert single_ms >= 0
    assert combo_ms >= 0
    # 留下 benchmark 输出供 CI 采集
    print(f"\n[benchmark] single_dimension={single_ms:.2f}ms  combination={combo_ms:.2f}ms")


def test_scene_coverage_performance_does_not_regress_beyond_threshold():
    """万级样本统计耗时不超过 500ms 性能基线阈值。"""
    import time

    from repositories.scene_label_repository import SceneLabelRepository

    repo = SceneLabelRepository()
    _seed_large_sample(repo)

    threshold_ms = 500  # 保守基线

    t0 = time.perf_counter()
    repo.stats_by_dimension(dataset_version_id="perf-ds:v1", dimension="weather")
    single_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    repo.stats_by_combinations(
        dataset_version_id="perf-ds:v1", dimensions=["time_of_day", "weather", "environment"]
    )
    combo_ms = (time.perf_counter() - t0) * 1000

    assert single_ms < threshold_ms, f"single dimension took {single_ms:.1f}ms (threshold={threshold_ms}ms)"
    assert combo_ms < threshold_ms, f"combination took {combo_ms:.1f}ms (threshold={threshold_ms}ms)"
