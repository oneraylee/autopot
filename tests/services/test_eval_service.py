def test_eval_script_success_with_valid_report(tmp_path):
    from services.eval_service import EvalService

    service = EvalService(
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

    result = service.run_evaluation(job_id="job-1", command=["python", "eval.py"])
    assert result["ok"] is True
    assert result["report"]["overall"]["business_kpi"] == 0.9


def test_eval_report_missing_required_field_fails(tmp_path):
    from services.eval_service import EvalService

    service = EvalService(
        output_dir=tmp_path,
        executor=lambda _command: {
            "exit_code": 0,
            "stdout": "ok",
            "stderr": "",
            "report": {"overall": {"kpi_components": []}, "by_scene": []},
        },
    )

    result = service.run_evaluation(job_id="job-1", command=["python", "eval.py"])
    assert result["ok"] is False
    assert result["error_code"] == "EVAL_FAILED"


def test_eval_script_non_zero_exit_maps_eval_failed(tmp_path):
    from services.eval_service import EvalService

    service = EvalService(
        output_dir=tmp_path,
        executor=lambda _command: {"exit_code": 2, "stdout": "", "stderr": "boom", "report": None},
    )

    result = service.run_evaluation(job_id="job-1", command=["python", "eval.py"])
    assert result["ok"] is False
    assert result["error_code"] == "EVAL_FAILED"


def test_eval_failure_logs_persisted(tmp_path):
    from services.eval_service import EvalService

    service = EvalService(
        output_dir=tmp_path,
        executor=lambda _command: {"exit_code": 2, "stdout": "std", "stderr": "err", "report": None},
    )
    result = service.run_evaluation(job_id="job-1", command=["python", "eval.py"])

    assert result["ok"] is False
    stdout_path = tmp_path / "job-1.stdout.log"
    stderr_path = tmp_path / "job-1.stderr.log"
    assert stdout_path.exists()
    assert stderr_path.exists()


# ===== Phase 3 Step 1: Audit Traceability =====


def test_eval_failure_persists_traceable_audit_record(tmp_path):
    """Eval failure record must include job_id, run_id, stdout_path, stderr_path, created_at."""
    from services.eval_service import EvalService

    service = EvalService(
        output_dir=tmp_path,
        executor=lambda _cmd: {"exit_code": 1, "stdout": "out", "stderr": "err", "report": None},
    )
    result = service.run_evaluation(job_id="job-audit", run_id="run-1", command=["eval"])

    assert result["ok"] is False
    assert result["job_id"] == "job-audit"
    assert result["run_id"] == "run-1"
    assert "stdout_path" in result
    assert "stderr_path" in result
    assert "created_at" in result


def test_eval_success_record_keeps_job_run_timestamp_context(tmp_path):
    """Eval success record must also include job_id, run_id, created_at."""
    from services.eval_service import EvalService

    service = EvalService(
        output_dir=tmp_path,
        executor=lambda _cmd: {
            "exit_code": 0,
            "stdout": "ok",
            "stderr": "",
            "report": {
                "overall": {"business_kpi": 0.9, "kpi_components": [{"name": "q", "score": 0.9}]},
                "by_scene": [{"scene": "default", "business_kpi": 0.9}],
            },
        },
    )
    result = service.run_evaluation(job_id="job-ok", run_id="run-2", command=["eval"])

    assert result["ok"] is True
    assert result["job_id"] == "job-ok"
    assert result["run_id"] == "run-2"
    assert "created_at" in result
