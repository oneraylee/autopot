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
