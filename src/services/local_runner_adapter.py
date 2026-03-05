from datetime import UTC, datetime


class LocalRunnerAdapter:
    def __init__(self, executor=None) -> None:
        self._executor = executor or (lambda _command: {"exit_code": 0, "stdout": "", "stderr": ""})

    def build_run_command(
        self,
        *,
        image: str,
        mounts: list[tuple[str, str]],
        envs: dict[str, str],
        train_args: list[str],
        gpu_devices: list[str],
    ) -> list[str]:
        command = ["docker", "run", "--rm"]
        for source, target in mounts:
            command.extend(["-v", f"{source}:{target}"])

        runtime_envs = dict(envs)
        runtime_envs["CUDA_VISIBLE_DEVICES"] = ",".join(gpu_devices)
        for key, value in runtime_envs.items():
            command.extend(["-e", f"{key}={value}"])

        command.append(image)
        command.extend(train_args)
        return command

    def run(self, *, command: list[str]) -> dict:
        started_at = datetime.now(UTC)
        raw = self._executor(command)
        finished_at = datetime.now(UTC)
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)

        exit_code = int(raw.get("exit_code", 1))
        stdout = str(raw.get("stdout", ""))
        stderr = str(raw.get("stderr", ""))
        lowered = f"{stdout}\n{stderr}".lower()

        error_code = None
        if "out of memory" in lowered:
            error_code = "TRAIN_OOM"
        elif "nan" in lowered:
            error_code = "TRAIN_NAN"
        elif exit_code != 0:
            error_code = "DATA_INVALID"

        return {
            "command": command,
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
            "error_code": error_code,
            "started_at": started_at.isoformat(timespec="seconds"),
            "finished_at": finished_at.isoformat(timespec="seconds"),
            "duration_ms": duration_ms,
        }
