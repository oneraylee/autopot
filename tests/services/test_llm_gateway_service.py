"""RED tests for LLMGatewayService (Step 5)."""
import os
import pytest
from datetime import datetime, UTC, timedelta


def _make_log_repo():
    from repositories.llm_call_log_repository import LLMCallLogRepository
    return LLMCallLogRepository()


def _make_gateway(log_repo=None):
    from services.llm_gateway_service import LLMGatewayService
    if log_repo is None:
        log_repo = _make_log_repo()
    return LLMGatewayService(call_log_repo=log_repo), log_repo


# ── Protocol mock helpers ───────────────────

class MockLLMProvider:
    """Mock LLMProvider implementing the Protocol."""

    def __init__(self, name: str = "mock", fail: bool = False, transient_fails: int = 0):
        self.name = name
        self._fail = fail
        self._transient_fails = transient_fails
        self._call_count = 0

    def chat(self, messages: list[dict], **kwargs) -> dict:
        self._call_count += 1
        if self._transient_fails > 0 and self._call_count <= self._transient_fails:
            raise RuntimeError("transient failure")
        if self._fail:
            raise RuntimeError("permanent failure")
        return {
            "content": "mock response",
            "usage": {"input_tokens": 100, "output_tokens": 50},
        }

    def models(self) -> list[str]:
        return ["mock-model"]


class MockEmbeddingProvider:
    """Mock EmbeddingProvider implementing the Protocol."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


# ── Tests ───────────────────────────────────

def test_provider_protocol_mockable():
    from services.llm_gateway_service import LLMGatewayService
    gw, _ = _make_gateway()
    mock = MockLLMProvider(name="test_provider")
    gw.register_provider("test_provider", mock)
    providers = gw.list_providers()
    assert "test_provider" in providers


def test_chat_completion_routes_to_correct_provider():
    gw, _ = _make_gateway()
    mock_openai = MockLLMProvider(name="openai")
    mock_zhipu = MockLLMProvider(name="zhipu")
    gw.register_provider("openai", mock_openai)
    gw.register_provider("zhipu", mock_zhipu)
    gw.set_route("agent_plan", provider_name="openai", model="gpt-4o")
    gw.set_route("skill_extract", provider_name="zhipu", model="glm-4-flash")

    result = gw.chat_completion(
        task_type="agent_plan",
        messages=[{"role": "user", "content": "hello"}],
    )
    assert result["content"] == "mock response"
    assert mock_openai._call_count == 1
    assert mock_zhipu._call_count == 0


def test_embed_calls_embedding_provider():
    gw, _ = _make_gateway()
    emb = MockEmbeddingProvider()
    gw.register_embedding_provider("openai", emb)
    gw.set_route("embedding", provider_name="openai", model="text-embedding-3-small")

    vectors = gw.embed(texts=["hello", "world"])
    assert len(vectors) == 2
    assert len(vectors[0]) == 3


def test_call_log_auto_written_after_completion():
    log_repo = _make_log_repo()
    gw, _ = _make_gateway(log_repo=log_repo)
    mock = MockLLMProvider(name="openai")
    gw.register_provider("openai", mock)
    gw.set_route("agent_plan", provider_name="openai", model="gpt-4o")

    gw.chat_completion(
        task_type="agent_plan",
        messages=[{"role": "user", "content": "test"}],
    )

    logs = log_repo.batch_query(offset=0, limit=10)
    assert len(logs) == 1
    assert logs[0]["call_type"] == "agent_plan"
    assert logs[0]["provider"] == "openai"
    assert logs[0]["model"] == "gpt-4o"


def test_invalid_task_type_returns_gateway_error():
    gw, _ = _make_gateway()
    mock = MockLLMProvider(name="openai")
    gw.register_provider("openai", mock)

    with pytest.raises(Exception) as exc:
        gw.chat_completion(
            task_type="nonexistent_type",
            messages=[{"role": "user", "content": "test"}],
        )
    assert "LLM_GATEWAY_ERROR" in str(exc.value) or "no route" in str(exc.value).lower()


def test_list_providers_returns_registered():
    gw, _ = _make_gateway()
    mock1 = MockLLMProvider(name="p1")
    mock2 = MockLLMProvider(name="p2")
    gw.register_provider("p1", mock1)
    gw.register_provider("p2", mock2)

    providers = gw.list_providers()
    assert set(providers) == {"p1", "p2"}


def test_rate_limit_triggers_wait():
    gw, _ = _make_gateway()
    mock = MockLLMProvider(name="openai")
    gw.register_provider("openai", mock)
    gw.set_route("agent_plan", provider_name="openai", model="gpt-4o")
    gw.set_rate_limit("openai", rpm=2, window_seconds=0.5)

    # First two should succeed immediately
    gw.chat_completion(task_type="agent_plan", messages=[{"role": "user", "content": "1"}])
    gw.chat_completion(task_type="agent_plan", messages=[{"role": "user", "content": "2"}])

    # Third should still succeed (rate limiter waits rather than rejects)
    result = gw.chat_completion(task_type="agent_plan", messages=[{"role": "user", "content": "3"}])
    assert result["content"] == "mock response"
    assert mock._call_count == 3


def test_retry_on_transient_failure():
    gw, _ = _make_gateway()
    mock = MockLLMProvider(name="openai", transient_fails=2)
    gw.register_provider("openai", mock)
    gw.set_route("agent_plan", provider_name="openai", model="gpt-4o")
    gw.set_retry(max_retries=3)

    result = gw.chat_completion(
        task_type="agent_plan",
        messages=[{"role": "user", "content": "test"}],
    )
    assert result["content"] == "mock response"
    assert mock._call_count == 3  # 2 fails + 1 success


def test_api_key_from_env_variable():
    from services.llm_gateway_service import LLMGatewayService

    os.environ["TEST_PROVIDER_API_KEY"] = "sk-test-secret-123"
    try:
        gw, _ = _make_gateway()
        key = gw.get_api_key("TEST_PROVIDER_API_KEY")
        assert key == "sk-test-secret-123"
    finally:
        del os.environ["TEST_PROVIDER_API_KEY"]


def test_usage_report_aggregation():
    log_repo = _make_log_repo()
    gw, _ = _make_gateway(log_repo=log_repo)
    mock = MockLLMProvider(name="openai")
    gw.register_provider("openai", mock)
    gw.set_route("agent_plan", provider_name="openai", model="gpt-4o")

    gw.chat_completion(task_type="agent_plan", messages=[{"role": "user", "content": "1"}])
    gw.chat_completion(task_type="agent_plan", messages=[{"role": "user", "content": "2"}])

    now = datetime.now(UTC)
    report = gw.get_usage_report(
        start_time=now - timedelta(minutes=5),
        end_time=now + timedelta(minutes=5),
    )
    assert len(report) >= 1
    openai_report = [r for r in report if r["provider"] == "openai"][0]
    assert openai_report["count"] == 2


def test_empty_time_range_returns_zero():
    log_repo = _make_log_repo()
    gw, _ = _make_gateway(log_repo=log_repo)
    mock = MockLLMProvider(name="openai")
    gw.register_provider("openai", mock)
    gw.set_route("agent_plan", provider_name="openai", model="gpt-4o")
    gw.chat_completion(task_type="agent_plan", messages=[{"role": "user", "content": "x"}])

    report = gw.get_usage_report(
        start_time=datetime(2099, 1, 1, tzinfo=UTC),
        end_time=datetime(2099, 1, 2, tzinfo=UTC),
    )
    assert len(report) == 0
