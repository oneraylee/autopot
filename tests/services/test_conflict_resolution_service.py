"""RED tests for ConflictResolutionService (Phase 3 Step 1)."""
import pytest


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_service(rules=None):
    from services.conflict_resolution_service import ConflictResolutionService
    return ConflictResolutionService(rules=rules or [])


# Sample techniques with metadata for tests
def _tech(tech_id, **kwargs):
    base = {
        "technique_id": tech_id,
        "name": tech_id,
        "category": "regularization",
        "layer": "training",
        "task_type": "det",
        "maturity": "stable",
        "default_priority": 3,
        "framework_version_min": "8.0",
        "conditions": [],
        "resources": {"gpu_mem_gb": 2.0, "cpu_cores": 1, "storage_gb": 0.1},
    }
    base.update(kwargs)
    return base


# ══════════════════════════════════════════════════════════════════════════════
# Step 1 – DSL 规则解析
# ══════════════════════════════════════════════════════════════════════════════

def test_dsl_rule_parse_valid():
    """JSON DSL 规则解析正确：有效规则可被加载不报错。"""
    from services.conflict_resolution_service import DSLRuleEngine
    rules = [
        {
            "rule_type": "incompatible_with",
            "if": {"all": [{"technique": "tech_a"}, {"technique": "tech_b"}]},
            "because": {"reason_code": "resource", "message": "memory too high"},
            "severity": "hard",
        }
    ]
    engine = DSLRuleEngine(rules=rules)
    assert len(engine.rules) == 1
    assert engine.rules[0]["rule_type"] == "incompatible_with"


def test_dsl_incompatible_with_matches():
    """incompatible_with 规则：同时包含 tech_a 和 tech_b → 标记为 hard 冲突被 rejected。"""
    rules = [
        {
            "rule_type": "incompatible_with",
            "if": {"all": [{"technique": "tech_a"}, {"technique": "tech_b"}]},
            "because": {"reason_code": "resource", "message": "memory too high"},
            "severity": "hard",
        }
    ]
    svc = _make_service(rules=rules)
    techniques = [_tech("tech_a"), _tech("tech_b")]
    result = svc.resolve(techniques)

    rejected_ids = [r["technique_id"] for r in result["rejected"]]
    assert "tech_b" in rejected_ids or "tech_a" in rejected_ids


# ══════════════════════════════════════════════════════════════════════════════
# Step 1 – 五类冲突
# ══════════════════════════════════════════════════════════════════════════════

def test_structural_conflict_rejected():
    """结构冲突：同一 target_path 且不可合并 → 至少一个被 rejected。"""
    rules = [
        {
            "rule_type": "structural",
            "if": {"all": [{"technique": "tech_head_a"}, {"technique": "tech_head_b"}]},
            "because": {"reason_code": "structural_conflict", "message": "same model position"},
            "severity": "hard",
        }
    ]
    svc = _make_service(rules=rules)
    techniques = [
        _tech("tech_head_a", target_path="model.head"),
        _tech("tech_head_b", target_path="model.head"),
    ]
    result = svc.resolve(techniques)
    assert len(result["rejected"]) >= 1
    assert any(r["reason_code"] == "structural_conflict" for r in result["rejected"])


def test_resource_conflict_over_budget_rejected():
    """资源冲突：叠加超出 gpu 预算 → rejected。"""
    svc = _make_service()
    techniques = [
        _tech("tech_large_imgsz", resources={"gpu_mem_gb": 16.0}),
        _tech("tech_large_backbone", resources={"gpu_mem_gb": 14.0}),
    ]
    constraints = {"gpu_mem_gb": 24}
    result = svc.resolve(techniques, runtime_constraints=constraints)
    # Combined usage is 30 GB > 24 GB budget
    rejected_ids = [r["technique_id"] for r in result["rejected"]]
    assert len(rejected_ids) >= 1
    assert any(r["reason_code"] == "resource_conflict" for r in result["rejected"])


def test_objective_conflict_kpi_weight_decision():
    """目标冲突：精度 KPI 权重决策 → 不满足约束的被 rejected。"""
    rules = [
        {
            "rule_type": "objective",
            "if": {"all": [{"technique": "tech_high_latency"}]},
            "constraint": {"latency_ms_max": 25},
            "because": {"reason_code": "objective_conflict", "message": "violates latency kpi"},
            "severity": "hard",
        }
    ]
    svc = _make_service(rules=rules)
    techniques = [_tech("tech_high_latency", latency_ms_est=50)]
    constraints = {"latency_ms_max": 25}
    result = svc.resolve(techniques, runtime_constraints=constraints)
    rejected_ids = [r["technique_id"] for r in result["rejected"]]
    assert "tech_high_latency" in rejected_ids


def test_version_conflict_filtered():
    """版本冲突：framework_version 不满足 → 直接过滤 (rejected)。"""
    svc = _make_service()
    techniques = [
        _tech("tech_new_feature", framework_version_min="9.0"),
    ]
    constraints = {"framework_version": "8.0"}
    result = svc.resolve(techniques, runtime_constraints=constraints)
    rejected_ids = [r["technique_id"] for r in result["rejected"]]
    assert "tech_new_feature" in rejected_ids
    assert any(r["reason_code"] == "version_conflict" for r in result["rejected"])


def test_lifecycle_conflict_condition_branch():
    """生命周期冲突：阶段约束 → 不适用阶段被剔除。"""
    svc = _make_service()
    techniques = [
        _tech("tech_finetuning_only", applicable_stage="finetune"),
    ]
    constraints = {"training_stage": "initial"}
    result = svc.resolve(techniques, runtime_constraints=constraints)
    rejected_ids = [r["technique_id"] for r in result["rejected"]]
    assert "tech_finetuning_only" in rejected_ids
    assert any(r["reason_code"] == "lifecycle_conflict" for r in result["rejected"])


# ══════════════════════════════════════════════════════════════════════════════
# Step 1 – Severity 与优先级
# ══════════════════════════════════════════════════════════════════════════════

def test_severity_affects_judgment():
    """severity=soft 不直接 rejected，可产生 warning。"""
    rules = [
        {
            "rule_type": "incompatible_with",
            "if": {"all": [{"technique": "tech_x"}, {"technique": "tech_y"}]},
            "because": {"reason_code": "soft_tradeoff", "message": "minor tradeoff"},
            "severity": "soft",
        }
    ]
    svc = _make_service(rules=rules)
    techniques = [_tech("tech_x"), _tech("tech_y")]
    result = svc.resolve(techniques)
    # soft severity: both may still be accepted, but a warning is issued
    assert len(result["rejected"]) == 0
    assert len(result["warnings"]) >= 1


def test_priority_ordering_correct():
    """优先级排序：安全 > KPI > 资源 > 结构 > 版本 > soft tradeoff。"""
    svc = _make_service()
    priorities = svc.conflict_priority_order()
    assert priorities.index("safety") < priorities.index("kpi_hard")
    assert priorities.index("kpi_hard") < priorities.index("resource_hard")
    assert priorities.index("resource_hard") < priorities.index("structural_hard")
    assert priorities.index("structural_hard") < priorities.index("version")
    assert priorities.index("version") < priorities.index("soft_tradeoff")


# ══════════════════════════════════════════════════════════════════════════════
# Step 1 – validate_combination 资源预算校验
# ══════════════════════════════════════════════════════════════════════════════

def test_validate_combination_gpu_mem_exceed():
    """多技能叠加显存超出 gpu_mem_gb → 返回 ok=False 并拒绝。"""
    svc = _make_service()
    techniques = [
        {"technique_id": "tech_a", "resources": {"gpu_mem_gb": 16.0}},
        {"technique_id": "tech_b", "resources": {"gpu_mem_gb": 12.0}},
    ]
    constraints = {"gpu_mem_gb": 24}
    result = svc.validate_combination(techniques=techniques, constraints=constraints)
    assert result["ok"] is False
    assert "gpu_mem_gb" in result["violation"]


def test_validate_combination_near_boundary_warning():
    """叠加接近边界（>80% 但未超出）→ ok=True + warning。"""
    svc = _make_service()
    techniques = [
        {"technique_id": "tech_a", "resources": {"gpu_mem_gb": 10.0}},
        {"technique_id": "tech_b", "resources": {"gpu_mem_gb": 10.0}},
    ]
    constraints = {"gpu_mem_gb": 24}
    result = svc.validate_combination(techniques=techniques, constraints=constraints)
    # 20/24 = 83%, above 80% but under 100%
    assert result["ok"] is True
    assert len(result["warnings"]) >= 1


def test_validate_combination_within_budget_pass():
    """叠加在预算 80% 以内 → ok=True + 无 warning。"""
    svc = _make_service()
    techniques = [
        {"technique_id": "tech_a", "resources": {"gpu_mem_gb": 5.0}},
        {"technique_id": "tech_b", "resources": {"gpu_mem_gb": 4.0}},
    ]
    constraints = {"gpu_mem_gb": 24}
    result = svc.validate_combination(techniques=techniques, constraints=constraints)
    assert result["ok"] is True
    assert len(result["warnings"]) == 0
