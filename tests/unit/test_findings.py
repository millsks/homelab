from __future__ import annotations

import pytest

from asgard_harness.findings import (
    CheckStatus,
    Finding,
    passed,
    report_of,
    result,
    skipped,
)


def test_a_finding_must_name_its_subject():
    with pytest.raises(ValueError, match="subject"):
        Finding(defect="d", subject="  ", detail="something")


@pytest.mark.parametrize("field", ["defect", "detail"])
def test_a_finding_must_carry_its_other_fields(field: str):
    kwargs = {"defect": "d", "subject": "s", "detail": "t"}
    kwargs[field] = ""
    with pytest.raises(ValueError, match=field):
        Finding(**kwargs)


def test_finding_render_names_subject_and_location():
    finding = Finding(defect="d", subject="KEY", detail="is wrong", location="file:3")
    assert finding.render() == "d: KEY (file:3) — is wrong"
    assert Finding(defect="d", subject="KEY", detail="is wrong").render() == "d: KEY — is wrong"


def test_passing_check_reports_what_it_examined():
    check = passed("Name", "defect", 7, "entries", note="all good")
    assert check.status is CheckStatus.PASSED
    assert check.render() == ["[PASS] Name: 7 entries examined — all good"]


def test_failing_check_lists_every_finding():
    check = result("Name", "d", 2, "rows", [Finding(defect="d", subject="row-1", detail="bad")])
    assert check.status is CheckStatus.FAILED
    lines = check.render()
    assert lines[0].startswith("[FAIL]")
    assert "row-1" in lines[1]


def test_skipped_check_is_not_a_pass():
    check = skipped("Name", "d", "rows", "no input")
    assert check.status is CheckStatus.SKIPPED
    assert check.render()[0] == "[SKIP] Name: 0 rows examined — no input"


def test_report_exit_code_and_summary():
    clean = report_of([passed("A", "d", 1, "x")])
    assert clean.exit_code == 0
    assert "1 checks run: 1 passed, 0 failed, 0 skipped; 0 defect(s) named." in clean.render()

    dirty = report_of(
        [passed("A", "d", 1, "x"), result("B", "d", 1, "x", [Finding(defect="d", subject="s", detail="t")])]
    )
    assert dirty.exit_code == 1
    assert len(dirty.findings) == 1
    assert [check.name for check in dirty.failed] == ["B"]


def test_report_as_dict_is_json_shaped():
    report = report_of([result("B", "d", 1, "x", [Finding(defect="d", subject="s", detail="t", location="f:1")])])
    payload = report.as_dict()
    assert payload["exit_code"] == 1
    checks = payload["checks"]
    assert isinstance(checks, list)
    assert checks[0]["findings"][0]["subject"] == "s"
