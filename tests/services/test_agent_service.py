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
