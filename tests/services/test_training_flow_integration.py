from pathlib import Path


def test_training_to_evidence_to_agent_flow_and_export(tmp_path: Path):
    from repositories.artifact_repository import ArtifactRepository
    from repositories.dataset_repository import DatasetRepository
    from repositories.job_repository import JobRepository
    from services.agent_service import AgentService
    from services.dataset_service import DatasetService
    from services.eval_service import EvalService
    from services.evidence_pack_builder import EvidencePackBuilderService
    from services.export_service import ExportService
    from services.job_service import JobService

    dataset_repository = DatasetRepository()
    job_repository = JobRepository()
    artifact_repository = ArtifactRepository()

    dataset_repository.create_dataset(dataset_id="ds-1", project_id="proj-1", name="raw")
    dataset_repository.create_dataset_version(dataset_id="ds-1", version=1, manifest_uri="s3://bucket/v1.json")
    dataset_repository.freeze_version(dataset_id="ds-1", version=1)

    job_service = JobService(job_repository=job_repository, dataset_repository=dataset_repository)
    job_service.create_and_queue_job(job_id="job-1", task_type="training", dataset_version_id="ds-1:v1")
    job_service.start_job(job_id="job-1", gpu_id="0")
    job_service.finish_job(job_id="job-1")

    dataset_service = DatasetService()
    dataset_report = dataset_service.get_dataset_report(
        [{"image_id": "img-1", "classes": ["car"], "bboxes": [[0, 0, 10, 10]], "scene": {"weather": "sunny"}}]
    )

    eval_service = EvalService(
        output_dir=tmp_path,
        executor=lambda _command: {
            "exit_code": 0,
            "stdout": "ok",
            "stderr": "",
            "report": {
                "overall": {"business_kpi": 0.9, "kpi_components": [{"name": "quality", "score": 0.9}]},
                "by_scene": [{"scene": "default", "business_kpi": 0.9}],
            },
        },
    )
    eval_result = eval_service.run_evaluation(job_id="job-1", command=["python", "eval.py"])

    evidence = EvidencePackBuilderService().build(
        dataset_report=dataset_report,
        job_summary=job_repository.get_job("job-1"),
        eval_report=eval_result["report"],
        kpi_config={"primary_kpi": "business_kpi", "threshold": 0.8},
        artifacts={"eval_report": "outputs/run-1/eval/eval_report.json"},
    )

    agent_output = {
        "analysis_report": "analysis",
        "next_experiments": {
            "experiments": [
                {
                    "name": "exp-A",
                    "changes": [{"field": "lr", "from": 0.001, "to": 0.0005}],
                    "expected": "better",
                    "evidence_refs": ["eval_report.overall.business_kpi"],
                }
            ]
        },
    }
    agent_result = AgentService().analyze(evidence_pack=evidence, agent_output=agent_output, baseline={"lr": 0.001})

    export_service = ExportService(
        job_repository=job_repository,
        artifact_repository=artifact_repository,
        executor=lambda _payload: {
            "exit_code": 0,
            "stdout": "ok",
            "stderr": "",
            "engine_locator": "outputs/run-1/export/model.engine",
        },
    )
    export_result = export_service.run_export(job_id="job-1", run_id="run-1", backend="tensorrt")

    assert job_repository.get_job("job-1")["status"] == "succeeded"
    assert eval_result["ok"] is True
    assert set(evidence.keys()) >= {"dataset_report", "job_summary", "eval_report", "kpi_config", "index_paths"}
    assert agent_result["ok"] is True
    assert agent_result["job_creation_triggered"] is False
    assert export_result["ok"] is True
    assert len(artifact_repository.list_artifacts(job_id="job-1", run_id="run-1", artifact_type="export")) == 1
