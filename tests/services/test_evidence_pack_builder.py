def test_evidence_pack_contains_four_core_inputs():
    from services.evidence_pack_builder import EvidencePackBuilderService

    service = EvidencePackBuilderService()
    evidence = service.build(
        dataset_report={"total_samples": 100},
        job_summary={"job_id": "job-1", "status": "succeeded"},
        eval_report={"overall": {"business_kpi": 0.9, "kpi_components": []}, "by_scene": []},
        kpi_config={"primary_kpi": "business_kpi", "threshold": 0.8},
        artifacts={"confusion_matrix": "outputs/run-1/confusion.png"},
    )

    assert set(evidence.keys()) >= {"dataset_report", "job_summary", "eval_report", "kpi_config", "index_paths"}


def test_curve_fields_are_summarized_or_downsampled():
    from services.evidence_pack_builder import EvidencePackBuilderService

    service = EvidencePackBuilderService(max_curve_points=5)
    evidence = service.build(
        dataset_report={"total_samples": 100},
        job_summary={"job_id": "job-1", "status": "succeeded"},
        eval_report={
            "overall": {"business_kpi": 0.9, "kpi_components": []},
            "by_scene": [],
            "curves": {"loss": list(range(20))},
        },
        kpi_config={"primary_kpi": "business_kpi", "threshold": 0.8},
        artifacts={},
    )

    assert len(evidence["eval_report"]["curves"]["loss"]) <= 5


def test_large_payload_fields_use_index_paths_not_inline():
    from services.evidence_pack_builder import EvidencePackBuilderService

    service = EvidencePackBuilderService()
    evidence = service.build(
        dataset_report={"total_samples": 100},
        job_summary={"job_id": "job-1", "status": "succeeded"},
        eval_report={"overall": {"business_kpi": 0.9, "kpi_components": []}, "by_scene": []},
        kpi_config={"primary_kpi": "business_kpi", "threshold": 0.8},
        artifacts={"large_tensor": "s3://bucket/tensors/abc"},
    )

    assert "large_tensor" in evidence["index_paths"]
    assert "large_tensor" not in evidence["eval_report"]
