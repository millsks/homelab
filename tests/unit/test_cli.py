from __future__ import annotations

import json
from pathlib import Path

import pytest

from asgard_harness import cli, selfcheck
from asgard_harness.findings import Finding, passed, report_of, result
from asgard_harness.workspace import Workspace


def test_parser_defaults_to_running_everything():
    args = cli.build_parser().parse_args([])
    assert args.command == "all"
    assert args.json is False


def test_parser_rejects_an_unknown_command():
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args(["nonsense"])


def test_audit_of_a_clean_mini_repository_exits_zero(mini: Workspace, monkeypatch, capsys):
    monkeypatch.setattr(Workspace, "git_commit_for", lambda self, path: "abc1234")
    assert cli.main(["audit", "--root", str(mini.root)]) == 0
    assert "Status enumeration" in capsys.readouterr().out


def test_audit_of_a_defective_repository_exits_non_zero(mini: Workspace, monkeypatch, capsys):
    monkeypatch.setattr(Workspace, "git_commit_for", lambda self, path: "abc1234")
    selfcheck.set_cell(mini.index_path, "PROC-ONE", 6, "`nearly`", anchor=selfcheck.ENTRY_ANCHOR)
    assert cli.main(["audit", "--root", str(mini.root)]) == 1
    assert "PROC-ONE" in capsys.readouterr().out


def test_json_output_is_one_parsable_event(mini: Workspace, monkeypatch, capsys):
    monkeypatch.setattr(Workspace, "git_commit_for", lambda self, path: "abc1234")
    cli.main(["audit", "--root", str(mini.root), "--json"])
    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert payload["exit_code"] == 0
    assert payload["command"] == "audit"


def test_drift_records_the_run(mini: Workspace, tmp_path: Path, capsys):
    record = tmp_path / "drift-record.json"
    assert cli.main(["drift", "--root", str(mini.root), "--record", str(record)]) == 0
    capsys.readouterr()
    payload = json.loads(record.read_text(encoding="utf-8"))
    assert payload["command"] == "drift"
    assert payload["checks"][0]["status"] == "skipped"


def test_all_runs_only_the_pure_readers(mini: Workspace, tmp_path: Path, monkeypatch, capsys):
    """`all` must never reach infrastructure: drift and converge are scheduled, not default."""
    monkeypatch.setattr(Workspace, "git_commit_for", lambda self, path: "abc1234")
    # The self-check's fixtures target the real repository's rows, so it is stubbed here; the
    # integration suite runs the real one. What this test asserts is which commands `all` runs.
    monkeypatch.setattr(cli, "run_self_check", lambda ws: report_of([passed("stub", "d", 0, "fixtures")]))
    record = tmp_path / "record.json"
    assert cli.main(["all", "--root", str(mini.root), "--record", str(record)]) == 0
    capsys.readouterr()
    assert {path.name for path in tmp_path.glob("*.json")} == {
        "audit-record.json",
        "selfcheck-record.json",
    }
    assert cli.GATE_COMMANDS == ("audit", "selfcheck")


def test_converge_is_available_but_not_run_by_default(mini: Workspace, capsys):
    assert "converge" in cli.COMMANDS
    assert "converge" not in cli.GATE_COMMANDS
    assert cli.main(["converge", "--root", str(mini.root)]) == 0
    assert "Convergence and idempotence" in capsys.readouterr().out


def test_emit_logs_an_error_line_when_defects_are_found(capsys):
    report = report_of([result("A", "d", 1, "x", [Finding(defect="d", subject="s", detail="t")])])
    cli.configure_logging(as_json=False)
    cli.emit(report, "audit", as_json=False)
    assert "defects found" in capsys.readouterr().out


def test_record_creates_missing_directories(tmp_path: Path):
    destination = tmp_path / "nested" / "deeper" / "record.json"
    cli.record(report_of([passed("A", "d", 1, "x")]), "audit", destination)
    assert json.loads(destination.read_text(encoding="utf-8"))["exit_code"] == 0
