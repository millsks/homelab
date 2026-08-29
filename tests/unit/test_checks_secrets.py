"""The plaintext-secret scan and the encryption policy that declares what must be encrypted.

Every credential-shaped literal in this file is **assembled at run time**, never written out. The
scan walks the whole tracked tree, `tests/` included, so a test that spelled out a private-key
header would fail the check it exists to prove — and the tempting fix, excluding the test suite
from the scan, would carve a hole in exactly the place a fixture is most likely to leave one.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from asgard_harness import defects
from asgard_harness.audit import run_audit, run_secrets
from asgard_harness.checks_secrets import (
    check_encryption_policy,
    is_sops_encrypted,
    run_secret_checks,
    scan_text,
)
from asgard_harness.findings import CheckStatus
from asgard_harness.secrets_policy import RECIPIENT_SENTINEL, CreationRule, EncryptionPolicy, load_policy
from asgard_harness.workspace import Workspace

# --- Assembled fixtures --------------------------------------------------------------------------

ARMOURED_KEY = "-----BEGIN OPENSSH " + "PRIVATE KEY-----"
AGE_IDENTITY = "AGE-SECRET-KEY-1" + "QWERTYUIOPASDFGHJKLZXCVBNM234567"
AWS_KEY_ID = "AKIA" + "Q3RSTUVWXY2345ZB"
GITHUB_TOKEN = "ghp_" + "a1b2c3d4e5f6g7h8i9j0K1L2M3N4O5P6Q7R8"
SLACK_TOKEN = "xoxb-" + "1234567890-abcdefghij"
JWT = "eyJhbGciOiJIUzI1NiJ9." + "eyJzdWIiOiIxMjM0NTY3ODkwIn0." + "dBjftJeZ4CVPmB92K27uhbUJU1p1r"
PROVIDER_KEY = "sk-" + "aB3dE5fG7hJ9kL1mN3pQ5rS7tU9vW1xY"
ASSIGNED = "DIRECTORY_BIND_TOKEN" + "=" + "Qx7mZ2pR9tL4vB8n"

SOPS_DOCUMENT = """bind_password: ENC[AES256_GCM,data:zzz,iv:xxx,tag:www,type:str]
sops:
    age:
        - recipient: age1exampletestrecipient
    lastmodified: "2026-01-01T00:00:00Z"
    mac: ENC[AES256_GCM,data:yyy,type:str]
    version: 3.13.3
"""
"""A minimal but structurally real SOPS document: ciphertext plus the `sops` block carrying a MAC."""

POLICY = """---
creation_rules:
  - path_regex: (^|/)[^/]+\\.sops\\.ya?ml$
    age: age1exampletestrecipient
"""


def build_tree(root: Path, files: dict[str, str], policy: str = POLICY) -> Workspace:
    """Write a throwaway repository with a `.sops.yaml` and some files.

    Args:
        root: Directory to build into.
        files: Repository-relative path to contents.
        policy: The `.sops.yaml` body.

    Returns:
        A workspace over it.
    """
    root.mkdir(parents=True, exist_ok=True)
    (root / ".sops.yaml").write_text(policy, encoding="utf-8")
    for relative, contents in files.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(contents, encoding="utf-8")
    return Workspace(root=root)


def results_by_defect(workspace: Workspace) -> dict[str, list[str]]:
    """Run the secret checks and index the subjects they named by defect class.

    Args:
        workspace: The workspace to scan.

    Returns:
        Defect class to the subjects named for it.
    """
    named: dict[str, list[str]] = {}
    for check in run_secret_checks(workspace, load_policy(workspace.root / ".sops.yaml")):
        for finding in check.findings:
            named.setdefault(finding.defect, []).append(finding.subject)
    return named


# --- Pattern detection ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("literal", "expected"),
    [
        (ARMOURED_KEY, "private-key-block"),
        (AGE_IDENTITY, "age-secret-key"),
        (AWS_KEY_ID, "aws-access-key-id"),
        (GITHUB_TOKEN, "github-token"),
        (SLACK_TOKEN, "slack-token"),
        (JWT, "json-web-token"),
        (PROVIDER_KEY, "provider-api-key"),
        (ASSIGNED, "credential-assignment"),
    ],
)
def test_every_pattern_fires_on_its_own_format(literal: str, expected: str):
    assert [name for _, (name) in [(line, pattern.name) for line, pattern in scan_text(literal)]] == [expected]


def test_the_line_number_is_the_one_the_secret_is_on():
    text = "\n".join(["clean", "clean", ASSIGNED, "clean"])
    assert [line for line, _ in scan_text(text)] == [3]


# The naming conventions a credential field actually appears in. Two successive boundary bugs each
# passed a single fixture that happened to share the fix's assumption — `\b` was proven with
# `password:` and missed `BIND_TOKEN=`; the lookbehind that fixed that was proven with `BIND_TOKEN=`
# and missed `bindPassword =`. One fixture per *shape*, not one standing in for the class, is what
# makes the next boundary change fail loudly instead of quietly narrowing the check.
VALUE = "Qx7mZ2pR9tL4vB8n"

SHAPES: tuple[tuple[str, str], ...] = (
    ("UPPER_SNAKE, unquoted", "DIRECTORY_BIND_TOKEN" + "=" + VALUE),
    ("UPPER_SNAKE, exported", "export API_KEY" + "=" + VALUE),
    ("lower_snake, colon", "directory_bind_password" + ": " + VALUE),
    ("lower_snake, equals with spaces", "access_key" + " = " + VALUE),
    ("camelCase, spaced equals", "bindPassword" + ' = "' + VALUE + '"'),
    ("camelCase, colon", "apiKey" + ": '" + VALUE + "'"),
    ("bare keyword, double quoted", "password" + '="' + VALUE + '"'),
    ("bare keyword, single quoted", "secret" + ": '" + VALUE + "'"),
    ("prefixed keyword", "mytoken" + ": " + VALUE),
    ("passphrase", "passphrase" + "=" + VALUE),
    # The exact string that reached the live repository undetected, kept verbatim as a fixture so
    # the regression has a name rather than being folded into the general case.
    ("reported regression", "DIRECTORY_BIND_TOKEN" + "=" + "s3cr3t-not-a-real" + "-token-abcdef123456"),
)


@pytest.mark.parametrize(("shape", "line"), SHAPES, ids=[shape for shape, _ in SHAPES])
def test_every_naming_shape_a_credential_field_takes_is_caught(shape: str, line: str):
    assert [pattern.name for _, pattern in scan_text(line)] == ["credential-assignment"], shape


def test_a_value_is_never_exempted_for_containing_a_credential_word():
    """The placeholder list must not hold field names: `in` exempts every value containing one.

    `s3cr3t-not-a-real-token-abcdef123456` was skipped because it contains `token`, which says
    nothing about the value and everything about the field beside it.
    """
    for word in ("token", "secret", "password", "credential", "vault", "sops"):
        line = "api_key" + "=" + f"aB3{word}9kL1mN3pQ5rS7"
        assert scan_text(line), word


@pytest.mark.parametrize(
    "line",
    [
        "password: ${VAULT_PASSWORD}",
        "password: {{ lookup('env', 'X') }}",
        "token: <see the escrow record>",
        "api_key: CHANGEME-before-first-run",
        "password: /var/run/secrets/path12",
        "secret: aaaaaaaaaaaaaaa1",
        "token: 1234567890123456",
        "password: abcdefghijklmnop",
        "password: short1",
        # The trailing guard still earns its place: these are words that merely start with a
        # keyword, and they are the reason a leading guard was reached for in the first place.
        "tokenizer: Qx7mZ2pR9tL4vB8n",
        "secretary: Qx7mZ2pR9tL4vB8n",
    ],
)
def test_references_placeholders_and_low_entropy_values_are_not_credentials(line: str):
    assert scan_text(line) == []


def test_the_scanner_does_not_match_its_own_source(repo_root: Path):
    """A pattern matching its own definition would fail the gate the moment it was written."""
    for module in ("checks_secrets.py", "secrets_policy.py", "selfcheck.py", "commit_message.py"):
        source = (repo_root / "src" / "asgard_harness" / module).read_text(encoding="utf-8")
        assert scan_text(source) == [], module


def test_sops_ciphertext_is_recognised():
    assert is_sops_encrypted(SOPS_DOCUMENT)
    assert is_sops_encrypted("A=ENC[AES256_GCM,data:abc,type:str]\nsops_mac=ENC[AES256_GCM,data:y]\n")
    assert not is_sops_encrypted("bind_password: plain")


def test_a_document_that_merely_mentions_the_marker_is_still_scanned():
    """A file judged encrypted is skipped entirely, so the marker alone must not be enough.

    This Runbook and this test both show samples of SOPS output. Treating either as ciphertext
    would be a documented way to smuggle a credential past the scan — which is what the first cut
    of `is_sops_encrypted` did.
    """
    prose = f"Encrypted values look like `ENC[AES256_GCM,data:abc,type:str]`.\n\n    {ARMOURED_KEY}\n"
    assert not is_sops_encrypted(prose)
    assert scan_text(prose)


# --- The policy ----------------------------------------------------------------------------------


def test_a_missing_policy_is_a_defect_not_an_empty_one(tmp_path: Path):
    policy = load_policy(tmp_path / ".sops.yaml")
    assert policy.present is False
    check = check_encryption_policy(policy, covered=0)
    assert check.status is CheckStatus.FAILED
    assert check.findings[0].defect == defects.UNDECLARED_ENCRYPTION_POLICY


@pytest.mark.parametrize(
    ("body", "fragment"),
    [
        ("---\nnot: [a, mapping\n", "could not be parsed as YAML"),
        ("---\n- just\n- a list\n", "does not parse to a mapping"),
        ("---\ncreation_rules: nope\n", "declares no 'creation_rules' list"),
        ("---\ncreation_rules: []\n", "empty 'creation_rules' list"),
    ],
)
def test_a_policy_that_declares_nothing_usable_is_reported(tmp_path: Path, body: str, fragment: str):
    path = tmp_path / ".sops.yaml"
    path.write_text(body, encoding="utf-8")
    check = check_encryption_policy(load_policy(path), covered=0)
    assert check.status is CheckStatus.FAILED
    assert fragment in check.findings[0].detail


@pytest.mark.parametrize(
    ("body", "fragment"),
    [
        ("---\ncreation_rules:\n  - just a string\n", "not a mapping"),
        ("---\ncreation_rules:\n  - age: age1x\n", "names no 'path_regex'"),
        ("---\ncreation_rules:\n  - path_regex: '[unclosed'\n", "not a usable regular expression"),
    ],
)
def test_an_unusable_rule_is_named(tmp_path: Path, body: str, fragment: str):
    path = tmp_path / ".sops.yaml"
    path.write_text(body, encoding="utf-8")
    check = check_encryption_policy(load_policy(path), covered=0)
    assert check.status is CheckStatus.FAILED
    assert fragment in check.findings[0].detail


def test_a_rule_that_could_not_compile_matches_nothing_rather_than_everything():
    rule = CreationRule(path_regex="[unclosed", recipients=(), error="broken")
    assert rule.matches("anything") is False


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("---\ncreation_rules:\n  - path_regex: x\n    age: one,two\n", ("one", "two")),
        ("---\ncreation_rules:\n  - path_regex: x\n    age:\n      - one\n      - two\n", ("one", "two")),
        ("---\ncreation_rules:\n  - path_regex: x\n", ()),
        ("---\ncreation_rules:\n  - path_regex: x\n    age: 7\n", ()),
    ],
)
def test_recipients_are_read_from_either_form(tmp_path: Path, body: str, expected: tuple[str, ...]):
    path = tmp_path / ".sops.yaml"
    path.write_text(body, encoding="utf-8")
    assert load_policy(path).rules[0].recipients == expected


def test_the_sentinel_passes_while_it_covers_nothing_and_fails_once_it_covers_something():
    policy = EncryptionPolicy(
        path=Path(".sops.yaml"),
        present=True,
        rules=(CreationRule(path_regex=r"\.sops\.yaml$", recipients=(RECIPIENT_SENTINEL,)),),
    )
    assert check_encryption_policy(policy, covered=0).status is CheckStatus.PASSED
    assert RECIPIENT_SENTINEL in check_encryption_policy(policy, covered=0).note

    fired = check_encryption_policy(policy, covered=1)
    assert fired.status is CheckStatus.FAILED
    assert RECIPIENT_SENTINEL in fired.findings[0].detail


def test_the_shipped_policy_does_not_cover_itself(repo_root: Path):
    """`.sops.yaml` is the public policy; a rule matching it would demand its own encryption."""
    policy = load_policy(repo_root / ".sops.yaml")
    assert policy.rules
    assert policy.rule_for(".sops.yaml") is None
    assert policy.rule_for("ansible/l0-physical/bind.sops.yaml") is not None


# --- The whole scan ------------------------------------------------------------------------------


def test_a_clean_tree_passes_and_says_what_it_scanned(tmp_path: Path):
    workspace = build_tree(tmp_path / "repo", {"docs/notes.md": "nothing to see\n"})
    checks = run_secret_checks(workspace, load_policy(workspace.root / ".sops.yaml"))
    assert [check.status for check in checks] == [CheckStatus.PASSED] * 3
    scan = checks[-1]
    assert scan.examined == 2
    assert "files scanned" in scan.noun
    assert "vendored trees not scanned" in scan.note


def test_a_plaintext_credential_is_rejected_and_the_path_is_named(tmp_path: Path):
    workspace = build_tree(tmp_path / "repo", {"ansible/l0-physical/vars.yml": f"a: 1\n{ASSIGNED}\n"})
    named = results_by_defect(workspace)
    assert named[defects.PLAINTEXT_SECRET] == ["ansible/l0-physical/vars.yml"]


def test_the_finding_never_echoes_the_secret_but_does_name_the_line(tmp_path: Path):
    workspace = build_tree(tmp_path / "repo", {"docs/leak.txt": f"x\n{ARMOURED_KEY}\n"})
    findings = [
        f for check in run_secret_checks(workspace, load_policy(workspace.root / ".sops.yaml")) for f in check.findings
    ]
    assert len(findings) == 1
    assert ARMOURED_KEY not in findings[0].detail
    assert findings[0].location == "docs/leak.txt:2"


def test_a_path_the_policy_covers_must_be_encrypted(tmp_path: Path):
    workspace = build_tree(tmp_path / "repo", {"ansible/l0-physical/bind.sops.yaml": "---\nbind_dn: uid=svc\n"})
    named = results_by_defect(workspace)
    assert named[defects.UNENCRYPTED_DECLARED_PATH] == ["ansible/l0-physical/bind.sops.yaml"]
    assert defects.PLAINTEXT_SECRET not in named


def test_an_encrypted_covered_path_passes_and_is_counted(tmp_path: Path):
    workspace = build_tree(
        tmp_path / "repo",
        {"ansible/l0-physical/bind.sops.yaml": SOPS_DOCUMENT},
    )
    checks = run_secret_checks(workspace, load_policy(workspace.root / ".sops.yaml"))
    assert [check.status for check in checks] == [CheckStatus.PASSED] * 3
    assert "1 encrypted" in checks[-1].note


def test_a_plaintext_pattern_inside_an_encrypted_file_is_not_reported(tmp_path: Path):
    """SOPS leaves the *keys* readable. A key named `password` is not a leaked password."""
    workspace = build_tree(
        tmp_path / "repo",
        {"ansible/l0-physical/bind.sops.yaml": f"note: {ASSIGNED}\n{SOPS_DOCUMENT}"},
    )
    assert results_by_defect(workspace) == {}


def test_a_file_that_cannot_be_decoded_is_named_and_not_counted_as_scanned(tmp_path: Path):
    workspace = build_tree(tmp_path / "repo", {"docs/notes.md": "clean\n"})
    (workspace.root / "docs" / "blob.bin").write_bytes(b"\xff\xfe\x00\x80binary")
    scan = run_secret_checks(workspace, load_policy(workspace.root / ".sops.yaml"))[-1]
    assert scan.examined == 2
    assert "docs/blob.bin" in scan.note
    assert "NOT scanned" in scan.note


def test_vendored_trees_are_excluded_and_the_exclusion_is_stated(tmp_path: Path):
    workspace = build_tree(tmp_path / "repo", {"_bmad/example.md": f"{ARMOURED_KEY}\n"})
    checks = run_secret_checks(workspace, load_policy(workspace.root / ".sops.yaml"))
    assert checks[-1].status is CheckStatus.PASSED
    assert "_bmad" in checks[-1].note


def test_the_walk_skips_caches_but_not_ordinary_directories(tmp_path: Path):
    workspace = build_tree(tmp_path / "repo", {"docs/notes.md": "clean\n"})
    (workspace.root / ".mypy_cache").mkdir()
    (workspace.root / ".mypy_cache" / "leak.txt").write_text(f"{ARMOURED_KEY}\n", encoding="utf-8")
    scanned = {workspace.relative(path) for path in workspace.scannable_files()[0]}
    assert scanned == {".sops.yaml", "docs/notes.md"}


def test_the_real_repository_scan_covers_untracked_files_too(repo_workspace: Workspace):
    paths, source = repo_workspace.scannable_files()
    assert source == "tracked and untracked files git would add (gitignored paths excluded)"
    assert paths
    assert not any(repo_workspace.is_vendored(repo_workspace.relative(path)) for path in paths)


def test_a_directory_that_is_not_a_repository_falls_back_to_walking(tmp_path: Path):
    workspace = build_tree(tmp_path / "repo", {"docs/notes.md": "clean\n"})
    _, source = workspace.scannable_files()
    assert "git could not answer" in source


# --- Wiring --------------------------------------------------------------------------------------


def test_the_gate_audit_runs_the_secret_checks_not_only_the_standalone_command(mini: Workspace, monkeypatch):
    """A check that only ever runs from a hook is a check a fresh clone does not have."""
    monkeypatch.setattr(Workspace, "git_commit_for", lambda self, path: "abc1234")
    names = {check.name for check in run_audit(mini).results}
    assert {"Encryption policy declared", "Declared paths are encrypted", "Plaintext secret material"} <= names


def test_the_standalone_command_runs_exactly_the_secret_checks(mini: Workspace):
    assert [check.name for check in run_secrets(mini).results] == [
        "Encryption policy declared",
        "Declared paths are encrypted",
        "Plaintext secret material",
    ]


# --- Enumeration failure paths -------------------------------------------------------------------
#
# A file list the harness could not obtain must fall back to walking, never to an empty list: an
# empty list scans nothing and reports PASS, which is the shape of failure this project keeps
# finding in its own gates.


def test_git_failing_to_list_falls_back_to_walking_rather_than_scanning_nothing(tmp_path: Path, monkeypatch):
    import asgard_harness.workspace as workspace_module

    workspace = build_tree(tmp_path / "repo", {"docs/notes.md": "clean\n"})

    def flaky(argv, **_kwargs):
        """A directory that *is* a repository, whose file list git then refuses to produce."""
        if "ls-files" in argv:
            return workspace_module.subprocess.CompletedProcess(argv, 128, "", "fatal: bad object")
        return workspace_module.subprocess.CompletedProcess(argv, 0, f"{workspace.root}\n", "")

    monkeypatch.setattr(workspace_module.subprocess, "run", flaky)
    monkeypatch.setattr(workspace_module.Path, "resolve", lambda self: workspace.root)
    paths, source = workspace.scannable_files()
    assert "git could not answer" in source
    assert {workspace.relative(path) for path in paths} == {".sops.yaml", "docs/notes.md"}


def test_git_that_cannot_be_launched_falls_back_to_walking(tmp_path: Path, monkeypatch):
    import asgard_harness.workspace as workspace_module

    workspace = build_tree(tmp_path / "repo", {"docs/notes.md": "clean\n"})

    def unlaunchable(*_args, **_kwargs):
        raise OSError("git is not installed")

    monkeypatch.setattr(workspace_module.subprocess, "run", unlaunchable)
    paths, source = workspace.scannable_files()
    assert "git could not answer" in source
    assert paths


def test_a_rule_block_that_is_not_a_mapping_declares_no_recipients():
    from asgard_harness.secrets_policy import _recipients_of

    assert _recipients_of("not a mapping") == ()
