def _build_routes():
    from api.proposal_routes import ProposalRoutes

    created_jobs = []

    def _create_training_job(request):
        created_jobs.append(request)
        return {"job_id": f"job-{len(created_jobs)}", "status": "created"}

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
    assert response["data"]["status"] == "created"
    assert response["data"]["audit"]["baseline_job_id"] == "job-base"
    assert len(created) == 1
    assert created[0]["baseline_job_id"] == "job-base"
    assert created[0]["candidate"]["name"] == "exp-1"


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


# ── Phase 1 Step 2: Proposal 校验契约统一门禁 ──


def _build_routes_with_artifacts():
    from api.proposal_routes import ProposalRoutes
    from repositories.artifact_repository import ArtifactRepository
    from repositories.job_repository import JobRepository

    artifact_repo = ArtifactRepository()
    job_repo = JobRepository()
    created_jobs = []

    def _create_training_job(request):
        created_jobs.append(request)
        return {"job_id": f"job-{len(created_jobs)}", "status": "created"}

    routes = ProposalRoutes(
        create_training_job=_create_training_job,
        artifact_repository=artifact_repo,
    )
    return routes, artifact_repo, job_repo, created_jobs


def test_validate_proposals_uses_job_id_and_run_id_to_resolve_artifacts():
    routes, artifact_repo, _, _ = _build_routes_with_artifacts()
    artifact_repo.register_artifact(
        job_id="job-1", run_id="run-1", artifact_type="llm", locator="llm/output.json"
    )
    routes.register_artifact_payload(
        job_id="job-1",
        run_id="run-1",
        artifact_type="llm",
        payload={
            "analysis_report": "analysis done",
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
        },
    )

    response = routes.validate_proposals({"job_id": "job-1", "run_id": "run-1"})

    assert response["ok"] is True
    data = response["data"]
    assert data["accepted"] == 1
    assert "candidates" in data
    assert data["baseline_job_id"] == "job-1"


def test_validate_proposals_returns_not_found_when_artifact_missing():
    routes, _, _, _ = _build_routes_with_artifacts()

    response = routes.validate_proposals({"job_id": "job-missing", "run_id": "run-1"})

    assert response["ok"] is False
    assert response["error"]["code"] in ("NOT_FOUND", "DATA_INVALID")


def test_validate_proposals_rejects_invalid_candidates_structure():
    routes, artifact_repo, _, _ = _build_routes_with_artifacts()
    artifact_repo.register_artifact(
        job_id="job-1", run_id="run-1", artifact_type="llm", locator="llm/output.json"
    )
    routes.register_artifact_payload(
        job_id="job-1",
        run_id="run-1",
        artifact_type="llm",
        payload={
            "analysis_report": "analysis done",
            "next_experiments": {
                "experiments": [
                    {
                        "name": "exp-1",
                        "changes": [{"field": "lr", "from": 0.001, "to": 0.0005}],
                        "expected": "higher kpi",
                    }
                ]
            },
        },
    )

    response = routes.validate_proposals({"job_id": "job-1", "run_id": "run-1"})

    assert response["ok"] is False


def test_next_experiments_http_shape_matches_appendix_spec():
    routes, artifact_repo, _, _ = _build_routes_with_artifacts()
    artifact_repo.register_artifact(
        job_id="job-1", run_id="run-1", artifact_type="llm", locator="llm/output.json"
    )
    routes.register_artifact_payload(
        job_id="job-1",
        run_id="run-1",
        artifact_type="llm",
        payload={
            "analysis_report": "analysis done",
            "next_experiments": {
                "experiments": [
                    {
                        "name": "exp-A",
                        "changes": [{"field": "lr", "from": 0.001, "to": 0.0005}],
                        "expected": "higher kpi",
                        "evidence_refs": ["eval_report.overall.business_kpi"],
                    }
                ]
            },
        },
    )

    response = routes.validate_proposals({"job_id": "job-1", "run_id": "run-1"})

    assert response["ok"] is True
    data = response["data"]
    assert "baseline_job_id" in data
    assert "candidates" in data
    assert isinstance(data["candidates"], list)
    assert data["candidates"][0]["name"] == "exp-A"


def test_create_from_proposal_accepts_candidate_shape_from_validate_result():
    routes, artifact_repo, _, created = _build_routes_with_artifacts()
    artifact_repo.register_artifact(
        job_id="job-1", run_id="run-1", artifact_type="llm", locator="llm/output.json"
    )
    routes.register_artifact_payload(
        job_id="job-1",
        run_id="run-1",
        artifact_type="llm",
        payload={
            "analysis_report": "analysis done",
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
        },
    )

    validate_result = routes.validate_proposals({"job_id": "job-1", "run_id": "run-1"})
    candidate = validate_result["data"]["candidates"][0]

    response = routes.create_from_proposal({
        "baseline_job_id": validate_result["data"]["baseline_job_id"],
        "who": "alice",
        "when": "2026-03-11",
        "confirmed": True,
        "candidate": candidate,
    })

    assert response["ok"] is True
    assert response["data"]["status"] == "created"
    assert len(created) == 1
