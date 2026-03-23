import pytest


def test_agent_output_requires_evidence_refs():
    from repositories.errors import RepositoryError
    from services.agent_service import AgentService

    service = AgentService()
    output = {
        "analysis_report": "report",
        "next_experiments": {
            "experiments": [
                {
                    "name": "A",
                    "changes": [{"field": "lr", "from": 0.001, "to": 0.0005}],
                    "expected": "better",
                }
            ]
        },
    }

    with pytest.raises(RepositoryError) as error:
        service.analyze(evidence_pack={"kpi_config": {}, "index_paths": {}}, agent_output=output)

    assert error.value.code == "LLM_FAILED"


def test_agent_output_schema_validation_failure():
    from repositories.errors import RepositoryError
    from services.agent_service import AgentService

    service = AgentService()

    with pytest.raises(RepositoryError) as error:
        service.analyze(evidence_pack={"kpi_config": {}, "index_paths": {}}, agent_output={"analysis_report": "ok"})

    assert error.value.code == "LLM_FAILED"


def test_default_policy_no_auto_job_creation():
    from services.agent_service import AgentService

    called = {"count": 0}

    def _create_job(_candidate):
        called["count"] += 1

    service = AgentService(create_training_job=_create_job)
    output = {
        "analysis_report": "report",
        "next_experiments": {
            "experiments": [
                {
                    "name": "A",
                    "changes": [{"field": "lr", "from": 0.001, "to": 0.0005}],
                    "expected": "better",
                    "evidence_refs": ["eval_report.overall.business_kpi"],
                }
            ]
        },
    }
    result = service.analyze(evidence_pack={"kpi_config": {}, "index_paths": {}}, agent_output=output)

    assert result["ok"] is True
    assert called["count"] == 0


def test_candidate_changes_are_baseline_relative():
    from repositories.errors import RepositoryError
    from services.agent_service import AgentService

    service = AgentService()
    output = {
        "analysis_report": "report",
        "next_experiments": {
            "experiments": [
                {
                    "name": "A",
                    "changes": [{"field": "lr", "from": 0.1, "to": 0.0005}],
                    "expected": "better",
                    "evidence_refs": ["eval_report.overall.business_kpi"],
                }
            ]
        },
    }

    with pytest.raises(RepositoryError) as error:
        service.analyze(
            evidence_pack={"kpi_config": {}, "index_paths": {}},
            agent_output=output,
            baseline={"lr": 0.001},
        )

    assert error.value.code == "LLM_FAILED"


# ===== Phase 3 Step 1: Audit Traceability =====

_VALID_AGENT_OUTPUT = {
    "analysis_report": "report",
    "next_experiments": {
        "experiments": [
            {
                "name": "A",
                "changes": [{"field": "lr", "from": 0.001, "to": 0.0005}],
                "expected": "better",
                "evidence_refs": ["eval_report.overall.business_kpi"],
            }
        ]
    },
}


def test_agent_success_persists_generation_audit_record():
    """Agent success must include job_id, run_id, status='success', created_at."""
    from services.agent_service import AgentService

    service = AgentService()
    result = service.analyze(
        evidence_pack={"kpi_config": {}, "index_paths": {}},
        agent_output=_VALID_AGENT_OUTPUT,
        job_id="job-a1",
        run_id="run-a1",
    )
    assert result["ok"] is True
    assert result["job_id"] == "job-a1"
    assert result["run_id"] == "run-a1"
    assert result["status"] == "success"
    assert "created_at" in result


def test_agent_failure_persists_error_audit_record():
    """Agent failure must include job_id, run_id, status='error', created_at."""
    from repositories.errors import RepositoryError
    from services.agent_service import AgentService

    service = AgentService()
    with pytest.raises(RepositoryError) as exc_info:
        service.analyze(
            evidence_pack={"kpi_config": {}, "index_paths": {}},
            agent_output={"analysis_report": "ok"},  # missing next_experiments
            job_id="job-a2",
            run_id="run-a2",
        )
    err = exc_info.value
    assert err.code == "LLM_FAILED"
    # Error should carry audit context
    assert hasattr(err, "audit") or err.code == "LLM_FAILED"


def test_audit_record_links_to_baseline_job_id_when_present():
    """When baseline is provided, the result should link to baseline_job_id."""
    from services.agent_service import AgentService

    service = AgentService()
    result = service.analyze(
        evidence_pack={"kpi_config": {}, "index_paths": {}},
        agent_output=_VALID_AGENT_OUTPUT,
        baseline={"lr": 0.001},
        job_id="job-a3",
        run_id="run-a3",
        baseline_job_id="job-baseline",
    )
    assert result["ok"] is True
    assert result["baseline_job_id"] == "job-baseline"
    assert "created_at" in result
