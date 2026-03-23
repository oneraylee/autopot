"""RED tests for LLMCallLogRepository (Step 4)."""
import pytest
from datetime import datetime, UTC, timedelta


def _make_repo():
    from repositories.llm_call_log_repository import LLMCallLogRepository
    return LLMCallLogRepository()


def _sample_log(**overrides):
    base = {
        "call_type": "agent_plan",
        "provider": "openai",
        "model": "gpt-4o",
        "input_tokens": 1500,
        "output_tokens": 500,
        "latency_ms": 1200,
        "cost_estimate": 0.032,
        "status": "success",
    }
    base.update(overrides)
    return base


def test_write_call_log_success():
    repo = _make_repo()
    log = repo.write_log(**_sample_log())
    assert log["call_type"] == "agent_plan"
    assert log["provider"] == "openai"
    assert log["model"] == "gpt-4o"
    assert log["input_tokens"] == 1500
    assert log["output_tokens"] == 500
    assert log["cost_estimate"] == 0.032
    assert log["status"] == "success"
    assert "call_id" in log
    assert "created_at" in log


def test_query_by_call_type_and_time_range():
    repo = _make_repo()
    repo.write_log(**_sample_log(call_type="agent_plan"))
    repo.write_log(**_sample_log(call_type="embedding"))
    repo.write_log(**_sample_log(call_type="agent_plan"))

    now = datetime.now(UTC)
    start = now - timedelta(minutes=5)
    end = now + timedelta(minutes=5)

    results = repo.query_logs(call_type="agent_plan", start_time=start, end_time=end)
    assert len(results) == 2
    assert all(r["call_type"] == "agent_plan" for r in results)


def test_aggregate_by_provider_model():
    repo = _make_repo()
    repo.write_log(**_sample_log(provider="openai", model="gpt-4o", input_tokens=100, output_tokens=50, cost_estimate=0.01))
    repo.write_log(**_sample_log(provider="openai", model="gpt-4o", input_tokens=200, output_tokens=100, cost_estimate=0.02))
    repo.write_log(**_sample_log(provider="zhipu", model="glm-4", input_tokens=300, output_tokens=150, cost_estimate=0.005))

    now = datetime.now(UTC)
    start = now - timedelta(minutes=5)
    end = now + timedelta(minutes=5)

    agg = repo.aggregate_usage(start_time=start, end_time=end)
    # Should have entries for two provider+model combos
    assert len(agg) == 2
    openai_agg = [a for a in agg if a["provider"] == "openai"][0]
    assert openai_agg["total_input_tokens"] == 300
    assert openai_agg["total_output_tokens"] == 150
    assert abs(openai_agg["total_cost"] - 0.03) < 1e-9


def test_batch_query_for_dashboard():
    repo = _make_repo()
    for i in range(15):
        repo.write_log(**_sample_log(input_tokens=i * 10))

    page1 = repo.batch_query(offset=0, limit=10)
    assert len(page1) == 10

    page2 = repo.batch_query(offset=10, limit=10)
    assert len(page2) == 5


def test_empty_time_range_returns_zero():
    repo = _make_repo()
    repo.write_log(**_sample_log())

    far_future_start = datetime(2099, 1, 1, tzinfo=UTC)
    far_future_end = datetime(2099, 1, 2, tzinfo=UTC)

    results = repo.query_logs(call_type="agent_plan", start_time=far_future_start, end_time=far_future_end)
    assert len(results) == 0

    agg = repo.aggregate_usage(start_time=far_future_start, end_time=far_future_end)
    assert len(agg) == 0
