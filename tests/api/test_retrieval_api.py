"""RED tests for Phase 3 API endpoints:
- POST /knowledge/retrieval/search
- POST /knowledge/retrieval/resolve-conflicts
- POST /knowledge/retrieval/compose-context
- GET  /llm-gateway/providers
- GET  /llm-gateway/usage
- GET  /llm-gateway/call-logs
"""
import pytest
from unittest.mock import MagicMock


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_knowledge_repo():
    from repositories.knowledge_repository import KnowledgeRepository
    return KnowledgeRepository()


def _seed_skills(repo, count=5):
    for i in range(count):
        repo.create_skill(
            skill_code=f"SK-{i:03d}",
            name=f"skill_{i}",
            category="regularization",
            layer="training",
            task_type="det",
            maturity="stable",
            default_priority=3,
            summary=f"Summary {i}",
        )


def _make_retrieval_routes():
    """Construct KnowledgeRoutes with Phase 3 retrieval services."""
    from api.knowledge_routes import KnowledgeRoutes
    from services.knowledge_retrieval_service import KnowledgeRetrievalService
    from services.conflict_resolution_service import ConflictResolutionService
    from services.strategy_composer_service import StrategyComposerService
    from services.knowledge_ingestion_service import KnowledgeIngestionService
    from services.knowledge_registry_service import KnowledgeRegistryService

    repo = _make_knowledge_repo()
    _seed_skills(repo)

    gw = MagicMock()
    ingestion = KnowledgeIngestionService(knowledge_repo=repo, llm_gateway=gw)
    registry = KnowledgeRegistryService(knowledge_repo=repo)
    retrieval = KnowledgeRetrievalService(knowledge_repo=repo)
    conflict = ConflictResolutionService()
    composer = StrategyComposerService(
        knowledge_repo=repo,
        retrieval_service=retrieval,
        conflict_service=conflict,
    )

    routes = KnowledgeRoutes(
        ingestion_service=ingestion,
        registry_service=registry,
        retrieval_service=retrieval,
        conflict_service=conflict,
        composer_service=composer,
    )
    return routes, repo


def _make_gateway_routes():
    """Construct LLMGatewayRoutes."""
    from api.llm_gateway_routes import LLMGatewayRoutes
    from services.llm_gateway_service import LLMGatewayService
    from repositories.llm_call_log_repository import LLMCallLogRepository

    call_log_repo = LLMCallLogRepository()
    gateway_svc = LLMGatewayService(call_log_repo=call_log_repo)

    # Register a provider
    provider = MagicMock()
    provider.models.return_value = ["gpt-4o"]
    gateway_svc.register_provider("openai", provider)
    gateway_svc.set_route("agent_plan", provider_name="openai", model="gpt-4o")

    # Add a few call logs
    call_log_repo.write_log(
        call_type="agent_plan", provider="openai", model="gpt-4o",
        input_tokens=100, output_tokens=50, latency_ms=200,
        cost_estimate=0.01, status="success",
    )

    return LLMGatewayRoutes(gateway_service=gateway_svc, call_log_repo=call_log_repo), call_log_repo


# ══════════════════════════════════════════════════════════════════════════════
# Step 4 – POST /knowledge/retrieval/search
# ══════════════════════════════════════════════════════════════════════════════

def test_post_retrieval_search_returns_candidates():
    """POST /knowledge/retrieval/search 返回候选技能列表。"""
    routes, _ = _make_retrieval_routes()
    payload = {
        "query_type": "dataset_plan",
        "query_signature": {
            "task_type": "det",
            "small_object_ratio": 0.31,
            "weak_scenes": ["night"],
        },
        "limit": 10,
    }
    response = routes.post_retrieval_search(payload)
    assert response["ok"] is True
    assert "candidates" in response["data"]
    assert isinstance(response["data"]["candidates"], list)


# ══════════════════════════════════════════════════════════════════════════════
# Step 4 – POST /knowledge/retrieval/resolve-conflicts
# ══════════════════════════════════════════════════════════════════════════════

def test_post_resolve_conflicts_returns_verdict():
    """POST /knowledge/retrieval/resolve-conflicts 返回 accepted / rejected。"""
    routes, repo = _make_retrieval_routes()
    payload = {
        "technique_ids": ["SK-000", "SK-001"],
        "runtime_constraints": {"gpu_mem_gb": 24},
    }
    response = routes.post_resolve_conflicts(payload)
    assert response["ok"] is True
    data = response["data"]
    assert "accepted" in data
    assert "rejected" in data


# ══════════════════════════════════════════════════════════════════════════════
# Step 4 – POST /knowledge/retrieval/compose-context
# ══════════════════════════════════════════════════════════════════════════════

def test_post_compose_context_returns_skill_context():
    """POST /knowledge/retrieval/compose-context 返回 SkillContext + snapshot_id。"""
    routes, _ = _make_retrieval_routes()
    payload = {
        "planning_type": "dataset_plan",
        "project_id": "proj_001",
        "dataset_report": {"task_type": "det", "stats": {}, "scene_gaps": []},
        "project_constraints": {"gpu_mem_gb": 24},
        "top_k": 5,
    }
    response = routes.post_compose_context(payload)
    assert response["ok"] is True
    data = response["data"]
    assert "snapshot_id" in data
    assert "context" in data
    ctx = data["context"]
    assert "candidate_techniques" in ctx
    assert "rejected_techniques" in ctx
    assert "conflict_summary" in ctx


# ══════════════════════════════════════════════════════════════════════════════
# Step 4 – GET /llm-gateway/providers
# ══════════════════════════════════════════════════════════════════════════════

def test_get_providers_list():
    """GET /llm-gateway/providers 返回已注册 Provider 列表。"""
    routes, _ = _make_gateway_routes()
    response = routes.get_providers()
    assert response["ok"] is True
    assert "providers" in response["data"]
    assert "openai" in response["data"]["providers"]


# ══════════════════════════════════════════════════════════════════════════════
# Step 4 – GET /llm-gateway/usage
# ══════════════════════════════════════════════════════════════════════════════

def test_get_usage_report_with_time_range():
    """GET /llm-gateway/usage 支持时间范围查询返回用量报表。"""
    routes, _ = _make_gateway_routes()
    response = routes.get_usage(params={})
    assert response["ok"] is True
    assert "usage" in response["data"]
    assert isinstance(response["data"]["usage"], list)


def test_get_usage_report_group_by():
    """GET /llm-gateway/usage 报表按 provider + model 分组。"""
    routes, _ = _make_gateway_routes()
    response = routes.get_usage(params={})
    assert response["ok"] is True
    usage = response["data"]["usage"]
    if usage:
        # Each entry should have provider and model
        assert "provider" in usage[0]
        assert "model" in usage[0]


# ══════════════════════════════════════════════════════════════════════════════
# Step 4 – GET /llm-gateway/call-logs
# ══════════════════════════════════════════════════════════════════════════════

def test_get_call_logs_pagination():
    """GET /llm-gateway/call-logs 支持分页（offset + limit）。"""
    routes, _ = _make_gateway_routes()
    response = routes.get_call_logs(params={"offset": 0, "limit": 1})
    assert response["ok"] is True
    data = response["data"]
    assert "logs" in data
    assert "total" in data
    assert len(data["logs"]) <= 1


def test_get_call_logs_filter_by_call_type():
    """GET /llm-gateway/call-logs 支持 call_type 过滤。"""
    routes, _ = _make_gateway_routes()
    response = routes.get_call_logs(params={"call_type": "agent_plan"})
    assert response["ok"] is True
    logs = response["data"]["logs"]
    for log in logs:
        assert log["call_type"] == "agent_plan"


def test_response_structure_consistent():
    """所有新 API 端点响应结构与现有 API 一致（ok + data / error）。"""
    routes, _ = _make_retrieval_routes()
    gw_routes, _ = _make_gateway_routes()

    # Check search
    ok_resp = routes.post_retrieval_search({
        "query_type": "dataset_plan",
        "query_signature": {"task_type": "det"},
    })
    assert "ok" in ok_resp and ok_resp["ok"] is True and "data" in ok_resp

    # Check invalid call returns error structure
    error_resp = routes.post_retrieval_search({})
    assert "ok" in error_resp and error_resp["ok"] is False
    assert "error" in error_resp
    assert "code" in error_resp["error"]
