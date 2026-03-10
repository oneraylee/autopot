def _build_routes():
    from api.proposal_routes import ProposalRoutes

    created_jobs = []

    def _create_training_job(candidate):
        created_jobs.append(candidate)
        return {"job_id": f"job-{len(created_jobs)}"}

    return ProposalRoutes(create_training_job=_create_training_job), created_jobs


def test_validate_proposals_success():
    routes, _ = _build_routes()

    response = routes.validate_proposals(
        {
            "analysis_report": "ok",
            "next_experiments": {
                "experiments": [
                    {
                        "name": "exp-1",
                        "changes": [{"field": "lr", "from": 0.001, "to": 0.0005}],
                        "expected": "higher kpi",
                        "evidence_refs": ["eval_report.overall.business_kpi"],
                    }
                ]
            },
        }
    )

    assert response["ok"] is True
    assert response["data"]["accepted"] == 1


def test_validate_proposals_missing_evidence_refs_rejected():
    routes, _ = _build_routes()

    response = routes.validate_proposals(
        {
            "analysis_report": "ok",
            "next_experiments": {
                "experiments": [
                    {
                        "name": "exp-1",
                        "changes": [{"field": "lr", "from": 0.001, "to": 0.0005}],
                        "expected": "higher kpi",
                    }
                ]
            },
        }
    )

    assert response["ok"] is False
    assert response["error"]["code"] == "LLM_FAILED"


def test_create_from_proposal_without_confirmation_rejected():
    routes, created = _build_routes()

    response = routes.create_from_proposal(
        {
            "candidate": {
                "name": "exp-1",
                "changes": [{"field": "lr", "from": 0.001, "to": 0.0005}],
                "expected": "higher kpi",
                "evidence_refs": ["eval_report.overall.business_kpi"],
            },
            "baseline_job_id": "job-base",
            "who": "alice",
            "when": "2026-03-06T10:00:00Z",
            "confirmed": False,
        }
    )

    assert response["ok"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"
    assert created == []


def test_create_from_proposal_success_after_confirmation():
    routes, created = _build_routes()

    response = routes.create_from_proposal(
        {
            "candidate": {
                "name": "exp-1",
                "changes": [{"field": "lr", "from": 0.001, "to": 0.0005}],
                "expected": "higher kpi",
                "evidence_refs": ["eval_report.overall.business_kpi"],
            },
            "baseline_job_id": "job-base",
            "who": "alice",
            "when": "2026-03-06T10:00:00Z",
            "confirmed": True,
            "idempotency_key": "idem-1",
        }
    )

    assert response["ok"] is True
    assert response["data"]["job_id"] == "job-1"
    assert response["data"]["audit"]["baseline_job_id"] == "job-base"
    assert len(created) == 1


def test_create_from_proposal_missing_baseline_job_id_rejected():
    routes, _ = _build_routes()

    response = routes.create_from_proposal(
        {
            "candidate": {
                "name": "exp-1",
                "changes": [{"field": "lr", "from": 0.001, "to": 0.0005}],
                "expected": "higher kpi",
                "evidence_refs": ["eval_report.overall.business_kpi"],
            },
            "who": "alice",
            "when": "2026-03-06T10:00:00Z",
            "confirmed": True,
        }
    )

    assert response["ok"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"


def test_create_from_proposal_idempotency_reuses_previous_result():
    routes, created = _build_routes()
    payload = {
        "candidate": {
            "name": "exp-1",
            "changes": [{"field": "lr", "from": 0.001, "to": 0.0005}],
            "expected": "higher kpi",
            "evidence_refs": ["eval_report.overall.business_kpi"],
        },
        "baseline_job_id": "job-base",
        "who": "alice",
        "when": "2026-03-06T10:00:00Z",
        "confirmed": True,
        "idempotency_key": "idem-1",
    }

    first = routes.create_from_proposal(payload)
    second = routes.create_from_proposal(payload)

    assert first["ok"] is True and second["ok"] is True
    assert first["data"]["job_id"] == second["data"]["job_id"]
    assert len(created) == 1
