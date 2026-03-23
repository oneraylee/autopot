from datetime import UTC, datetime
from pathlib import Path

from common.schema_validators import validate_payload


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class EvalService:
    def __init__(self, *, output_dir, executor=None) -> None:
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._executor = executor or (lambda _command: {"exit_code": 0, "stdout": "", "stderr": "", "report": None})

    def run_evaluation(self, *, job_id: str, command: list[str], run_id: str = "") -> dict:
        raw = self._executor(command)
        exit_code = int(raw.get("exit_code", 1))
        stdout = str(raw.get("stdout", ""))
        stderr = str(raw.get("stderr", ""))
        created_at = _now()

        if exit_code != 0:
            self._persist_logs(job_id=job_id, stdout=stdout, stderr=stderr)
            return {
                "ok": False,
                "error_code": "EVAL_FAILED",
                "job_id": job_id,
                "run_id": run_id,
                "stdout_path": str(self._stdout_path(job_id)),
                "stderr_path": str(self._stderr_path(job_id)),
                "created_at": created_at,
            }

        report = raw.get("report")
        validation = validate_payload("eval_report", report)
        if validation["ok"] is not True:
            self._persist_logs(job_id=job_id, stdout=stdout, stderr=stderr)
            return {
                "ok": False,
                "error_code": "EVAL_FAILED",
                "errors": validation.get("errors", []),
                "job_id": job_id,
                "run_id": run_id,
                "stdout_path": str(self._stdout_path(job_id)),
                "stderr_path": str(self._stderr_path(job_id)),
                "created_at": created_at,
            }

        return {
            "ok": True,
            "report": report,
            "stdout": stdout,
            "stderr": stderr,
            "job_id": job_id,
            "run_id": run_id,
            "created_at": created_at,
        }

    def _persist_logs(self, *, job_id: str, stdout: str, stderr: str) -> None:
        self._stdout_path(job_id).write_text(stdout, encoding="utf-8")
        self._stderr_path(job_id).write_text(stderr, encoding="utf-8")

    def _stdout_path(self, job_id: str) -> Path:
        return self._output_dir / f"{job_id}.stdout.log"

    def _stderr_path(self, job_id: str) -> Path:
        return self._output_dir / f"{job_id}.stderr.log"
