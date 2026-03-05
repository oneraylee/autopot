def test_build_run_command_includes_mounts_and_envs():
    from services.local_runner_adapter import LocalRunnerAdapter

    adapter = LocalRunnerAdapter()
    command = adapter.build_run_command(
        image="train:latest",
        mounts=[("/data", "/workspace/data"), ("/out", "/workspace/out")],
        envs={"ENV": "prod", "EPOCHS": "10"},
        train_args=["--lr", "0.001", "--batch-size", "16"],
        gpu_devices=["0", "1"],
    )

    joined = " ".join(command)
    assert "-v /data:/workspace/data" in joined
    assert "-e ENV=prod" in joined
    assert "CUDA_VISIBLE_DEVICES=0,1" in joined
    assert "--lr 0.001" in joined


def test_error_mapping_for_train_oom():
    from services.local_runner_adapter import LocalRunnerAdapter

    adapter = LocalRunnerAdapter(
        executor=lambda _command: {"exit_code": 137, "stdout": "", "stderr": "CUDA out of memory"}
    )

    result = adapter.run(command=["python", "train.py"])
    assert result["error_code"] == "TRAIN_OOM"


def test_error_mapping_for_train_nan():
    from services.local_runner_adapter import LocalRunnerAdapter

    adapter = LocalRunnerAdapter(
        executor=lambda _command: {"exit_code": 1, "stdout": "loss=nan", "stderr": ""}
    )

    result = adapter.run(command=["python", "train.py"])
    assert result["error_code"] == "TRAIN_NAN"


def test_non_zero_exit_code_standardized():
    from services.local_runner_adapter import LocalRunnerAdapter

    adapter = LocalRunnerAdapter(
        executor=lambda _command: {"exit_code": 3, "stdout": "", "stderr": "unknown failure"}
    )

    result = adapter.run(command=["python", "train.py"])
    assert result["error_code"] == "DATA_INVALID"


def test_runner_result_contains_trace_fields():
    from services.local_runner_adapter import LocalRunnerAdapter

    adapter = LocalRunnerAdapter(
        executor=lambda _command: {"exit_code": 0, "stdout": "ok", "stderr": ""}
    )

    result = adapter.run(command=["python", "train.py"])
    assert set(result.keys()) == {
        "command",
        "exit_code",
        "stdout",
        "stderr",
        "error_code",
        "started_at",
        "finished_at",
        "duration_ms",
    }
