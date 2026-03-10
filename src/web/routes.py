from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse


def _to_http(result: dict[str, Any]) -> JSONResponse:
    if result.get("ok") is True:
        return JSONResponse(status_code=200, content=result)

    code = result.get("error", {}).get("code", "SYSTEM_ERROR")
    status_code = 400
    if code == "NOT_FOUND":
        status_code = 404
    elif code == "CONFLICT":
        status_code = 409
    elif code == "SYSTEM_ERROR":
        status_code = 500
    return JSONResponse(status_code=status_code, content=result)


def build_router(container) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health() -> dict[str, Any]:
        return {"ok": True, "data": {"status": "up"}}

    @router.get("/projects/{project_id}/kpi-config")
    def get_project_kpi_config(project_id: str) -> JSONResponse:
        return _to_http(container.project_routes.get_project_kpi_config(project_id))

    @router.put("/projects/{project_id}/kpi-config")
    def put_project_kpi_config(project_id: str, payload: dict[str, Any]) -> JSONResponse:
        return _to_http(container.project_routes.put_project_kpi_config(project_id, payload))

    @router.post("/datasets/{dataset_id}/versions/import")
    def import_dataset_version(dataset_id: str, payload: dict[str, Any]) -> JSONResponse:
        return _to_http(container.dataset_routes.import_dataset_version(dataset_id, payload))

    @router.post("/datasets/{dataset_id}/versions/{version}/freeze")
    def freeze_dataset_version(dataset_id: str, version: int) -> JSONResponse:
        return _to_http(container.dataset_routes.freeze_dataset_version(dataset_id, version))

    @router.put("/datasets/versions/{dataset_version_id}/scene-labels")
    def upsert_scene_labels(dataset_version_id: str, payload: dict[str, Any]) -> JSONResponse:
        labels = payload.get("labels", []) if isinstance(payload, dict) else []
        return _to_http(container.dataset_routes.upsert_scene_labels(dataset_version_id, labels))

    @router.get("/datasets/versions/{dataset_version_id}/scene-coverage")
    def get_scene_coverage(
        dataset_version_id: str,
        dimensions: list[str] = Query(default=[]),
    ) -> JSONResponse:
        return _to_http(container.dataset_routes.get_scene_coverage(dataset_version_id, dimensions))

    @router.post("/jobs")
    def create_job(payload: dict[str, Any]) -> JSONResponse:
        return _to_http(container.job_routes.create_job(payload))

    @router.get("/jobs/{job_id}")
    def get_job(job_id: str) -> JSONResponse:
        return _to_http(container.job_routes.get_job(job_id))

    @router.post("/jobs/{job_id}/start")
    def start_job(job_id: str, payload: dict[str, Any]) -> JSONResponse:
        return _to_http(container.job_routes.start_job(job_id, gpu_id=str(payload.get("gpu_id", ""))))

    @router.post("/jobs/{job_id}/logs")
    def append_job_log(job_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        container.job_routes.append_log(job_id, str(payload.get("message", "")))
        return {"ok": True, "data": {"appended": True}}

    @router.get("/jobs/{job_id}/logs")
    def get_job_logs(job_id: str, page: int = 1, page_size: int = 20) -> JSONResponse:
        return _to_http(container.job_routes.get_logs(job_id, page=page, page_size=page_size))

    @router.post("/jobs/{job_id}/metrics")
    def record_job_metric(job_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        container.job_routes.record_metric(
            job_id,
            ts=int(payload.get("ts", 0)),
            values=payload.get("values", {}),
        )
        return {"ok": True, "data": {"recorded": True}}

    @router.get("/jobs/{job_id}/metrics")
    def get_job_metrics(job_id: str, start_ts: int, end_ts: int) -> JSONResponse:
        return _to_http(container.job_routes.get_metrics(job_id, start_ts=start_ts, end_ts=end_ts))

    @router.get("/jobs/{job_id}/artifacts/eval-report")
    def get_eval_report(job_id: str, run_id: str) -> JSONResponse:
        return _to_http(container.analysis_routes.get_eval_report(job_id, run_id=run_id))

    @router.get("/jobs/{job_id}/artifacts/evidence-pack")
    def get_evidence_pack(job_id: str, run_id: str) -> JSONResponse:
        return _to_http(container.analysis_routes.get_evidence_pack(job_id, run_id=run_id))

    @router.get("/jobs/{job_id}/artifacts/analysis-report")
    def get_analysis_report(job_id: str, run_id: str) -> JSONResponse:
        return _to_http(container.analysis_routes.get_analysis_report(job_id, run_id=run_id))

    @router.get("/jobs/{job_id}/artifacts/next-experiments")
    def get_next_experiments(job_id: str, run_id: str) -> JSONResponse:
        return _to_http(container.analysis_routes.get_next_experiments(job_id, run_id=run_id))

    @router.post("/proposals/validate")
    def validate_proposals(payload: dict[str, Any]) -> JSONResponse:
        return _to_http(container.proposal_routes.validate_proposals(payload))

    @router.post("/proposals/create-from-candidate")
    def create_from_candidate(payload: dict[str, Any]) -> JSONResponse:
        return _to_http(container.proposal_routes.create_from_proposal(payload))

    @router.post("/exports")
    def create_export(payload: dict[str, Any]) -> JSONResponse:
        return _to_http(container.export_routes.create_export(payload))

    @router.get("/exports/{export_id}")
    def get_export_status(export_id: str) -> JSONResponse:
        return _to_http(container.export_routes.get_export_status(export_id))

    @router.get("/exports/{export_id}/deploy-benchmark")
    def get_deploy_benchmark(export_id: str) -> JSONResponse:
        return _to_http(container.export_routes.get_deploy_benchmark(export_id))

    return router
