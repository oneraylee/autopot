from typing import Any

from api._response import error, run_with_error_mapping


class ProjectRoutes:
    _ALLOWED_OPERATORS = {"<", "<=", ">", ">=", "=="}

    def __init__(self, *, project_repository) -> None:
        self._project_repository = project_repository
        self._configs: dict[str, dict[str, Any]] = {}

    def get_project_kpi_config(self, project_id: str) -> dict[str, Any]:
        def _query() -> dict[str, Any]:
            self._project_repository.get_project(project_id)
            config = self._configs.get(project_id)
            if config is None:
                raise ValueError("kpi config not found")
            return {"project_id": project_id, **config}

        response = run_with_error_mapping(_query)
        if response["ok"] is False and response["error"]["code"] == "VALIDATION_ERROR":
            return error(code="NOT_FOUND", message="kpi config not found")
        return response

    def put_project_kpi_config(self, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        def _update() -> dict[str, Any]:
            self._project_repository.get_project(project_id)
            self._validate_payload(payload)
            version = len([pid for pid in self._configs if pid == project_id]) + 1
            self._project_repository.save_kpi_config(
                project_id,
                {
                    "primary_kpi": payload["primary_kpi"],
                    "threshold": payload["threshold"],
                },
                version=version,
            )
            self._configs[project_id] = {
                "primary_kpi": payload["primary_kpi"],
                "threshold": float(payload["threshold"]),
                "weights": payload["weights"],
                "deploy_constraints": payload.get("deploy_constraints", []),
            }
            return {"project_id": project_id, **self._configs[project_id]}

        return run_with_error_mapping(_update)

    def _validate_payload(self, payload: dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            raise ValueError("payload must be dict")

        primary_kpi = payload.get("primary_kpi")
        threshold = payload.get("threshold")
        weights = payload.get("weights")
        constraints = payload.get("deploy_constraints", [])

        if not isinstance(primary_kpi, str) or primary_kpi.strip() == "":
            raise ValueError("primary_kpi is required")
        if not isinstance(threshold, (int, float)):
            raise ValueError("threshold must be numeric")
        if not isinstance(weights, dict):
            raise ValueError("weights must be dict")

        eval_weight = float(weights.get("eval", -1))
        deploy_weight = float(weights.get("deploy", -1))
        if eval_weight < 0 or deploy_weight < 0 or abs((eval_weight + deploy_weight) - 1.0) > 1e-8:
            raise ValueError("weights must sum to 1.0")

        if not isinstance(constraints, list):
            raise ValueError("deploy_constraints must be list")
        for item in constraints:
            if not isinstance(item, dict):
                raise ValueError("constraint must be dict")
            if item.get("operator") not in self._ALLOWED_OPERATORS:
                raise ValueError("invalid constraint operator")
            if not isinstance(item.get("value"), (int, float)):
                raise ValueError("constraint value must be numeric")
