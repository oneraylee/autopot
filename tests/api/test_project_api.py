from repositories.project_repository import ProjectRepository


def _build_routes():
    from api.project_routes import ProjectRoutes

    repo = ProjectRepository()
    repo.create_project(project_id="proj-1", name="demo", owner="owner")
    return ProjectRoutes(project_repository=repo)


def test_get_project_kpi_config_success():
    routes = _build_routes()
    payload = {
        "primary_kpi": "business_kpi",
        "threshold": 0.8,
        "weights": {"eval": 0.7, "deploy": 0.3},
        "deploy_constraints": [{"metric": "latency_p95_ms", "operator": "<=", "value": 30.0}],
    }
    routes.put_project_kpi_config("proj-1", payload)

    response = routes.get_project_kpi_config("proj-1")

    assert response["ok"] is True
    assert response["data"]["project_id"] == "proj-1"
    assert response["data"]["weights"] == {"eval": 0.7, "deploy": 0.3}


def test_put_project_kpi_config_success_and_readback():
    routes = _build_routes()
    payload = {
        "primary_kpi": "business_kpi",
        "threshold": 0.75,
        "weights": {"eval": 0.6, "deploy": 0.4},
        "deploy_constraints": [{"metric": "latency_p95_ms", "operator": "<=", "value": 25.0}],
    }

    put_response = routes.put_project_kpi_config("proj-1", payload)
    get_response = routes.get_project_kpi_config("proj-1")

    assert put_response["ok"] is True
    assert get_response["ok"] is True
    assert get_response["data"]["threshold"] == 0.75


def test_put_project_kpi_config_invalid_weights_rejected():
    routes = _build_routes()

    response = routes.put_project_kpi_config(
        "proj-1",
        {
            "primary_kpi": "business_kpi",
            "threshold": 0.75,
            "weights": {"eval": 0.9, "deploy": 0.3},
            "deploy_constraints": [{"metric": "latency_p95_ms", "operator": "<=", "value": 25.0}],
        },
    )

    assert response["ok"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"


def test_put_project_kpi_config_invalid_constraint_operator_rejected():
    routes = _build_routes()

    response = routes.put_project_kpi_config(
        "proj-1",
        {
            "primary_kpi": "business_kpi",
            "threshold": 0.75,
            "weights": {"eval": 0.7, "deploy": 0.3},
            "deploy_constraints": [{"metric": "latency_p95_ms", "operator": "~", "value": 25.0}],
        },
    )

    assert response["ok"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"


def test_get_project_kpi_config_project_not_found():
    routes = _build_routes()

    response = routes.get_project_kpi_config("proj-404")

    assert response["ok"] is False
    assert response["error"]["code"] == "NOT_FOUND"
    assert set(response["error"]) == {"code", "message", "details", "type"}
