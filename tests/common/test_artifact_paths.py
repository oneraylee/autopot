import pytest

from common.artifact_paths import RunArtifacts


def test_core_directories_are_stable():
    artifacts = RunArtifacts(base_dir="/tmp/artifacts", run_id="run_001")
    dirs = artifacts.directories()

    assert dirs == {
        "run_dir": "/tmp/artifacts/run_001",
        "weights": "/tmp/artifacts/run_001/weights",
        "eval": "/tmp/artifacts/run_001/eval",
        "evidence": "/tmp/artifacts/run_001/evidence",
        "llm": "/tmp/artifacts/run_001/llm",
        "export": "/tmp/artifacts/run_001/export",
    }


def test_same_run_id_is_idempotent():
    first = RunArtifacts(base_dir="/tmp/a", run_id="run_777").to_index()
    second = RunArtifacts(base_dir="/tmp/a", run_id="run_777").to_index()
    assert first == second


def test_key_artifact_getters_are_stable():
    artifacts = RunArtifacts(base_dir="/tmp/root", run_id="run_x")
    assert artifacts.eval_report_path().endswith("/eval/eval_report.json")
    assert artifacts.evidence_pack_path().endswith("/evidence/evidence_pack.json")
    assert artifacts.analysis_report_path().endswith("/llm/analysis_report.md")


def test_index_export_is_serializable_shape():
    artifacts = RunArtifacts(base_dir="/tmp/root", run_id="run_serial")
    index = artifacts.to_index()

    expected_keys = {
        "run_id",
        "run_dir",
        "weights_dir",
        "eval_dir",
        "evidence_dir",
        "llm_dir",
        "export_dir",
        "eval_report",
        "evidence_pack",
        "analysis_report",
    }
    assert expected_keys.issubset(set(index.keys()))


def test_reject_empty_run_id():
    with pytest.raises(ValueError):
        RunArtifacts(base_dir="/tmp/x", run_id="")


def test_reject_path_traversal_run_id():
    with pytest.raises(ValueError):
        RunArtifacts(base_dir="/tmp/x", run_id="../escape")


def test_reject_illegal_characters_in_run_id():
    with pytest.raises(ValueError):
        RunArtifacts(base_dir="/tmp/x", run_id="run:001")
