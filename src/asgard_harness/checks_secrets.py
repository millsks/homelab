"""The plaintext-secret check, and the enforcement of the committed encryption policy.

Three rules, each the executable form of a sentence the architecture already states:

- **No plaintext credential reaches the Repository.** A secret in git history survives its own
  deletion, and rewriting the history of a public repository others may have cloned is not a
  remedy. So the rejection has to happen before the commit exists.
- **A path the policy says is encrypted is encrypted.** `.sops.yaml` declaring a rule that nothing
  enforces is operator memory wearing a configuration file's clothes.
- **The policy exists and declares something.** A deleted or emptied `.sops.yaml` would otherwise
  leave the first two rules covering nothing while every check still reported PASS.

**The scan never echoes what it found.** It names the file, the line, and the pattern. Printing the
matched text would copy the credential into the CI log of a public repository, turning the detector
into a second disclosure — and CI logs are exactly the place nobody thinks to redact.

**Detection is pattern-based, not entropy-based, on purpose.** An entropy scanner fires on lock
files, checksums, and base64 test data, and a check that cries wolf is a check people learn to
skip. Every pattern here matches a credential *format* that is not plausibly anything else. The
cost is real and is stated rather than glossed: a password with no recognisable shape, sitting in a
field this file does not name, passes. That is why encryption is declarative as well — the two
rules cover different halves of the problem.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from asgard_harness import defects
from asgard_harness.findings import CheckResult, Finding, result
from asgard_harness.secrets_policy import RECIPIENT_SENTINEL, EncryptionPolicy
from asgard_harness.workspace import VENDORED_ROOTS, Workspace

SOPS_CIPHERTEXT_MARKER = "ENC[AES256_GCM,"
"""What every SOPS-encrypted value carries, in both the YAML and the JSON output forms.

A file containing it has been through `sops --encrypt`, so its values are ciphertext and the
plaintext patterns below have nothing to say about it. Note what SOPS does *not* encrypt: the keys.
`directory_bind_password: ENC[AES256_GCM,...]` still tells a reader what the value is for, which is
a deliberate property of the format and not a leak.
"""


@dataclass(frozen=True, slots=True)
class SecretPattern:
    """One credential format, and why a match is not plausibly innocent.

    Attributes:
        name: The format's name, reported instead of the matched text.
        regex: What identifies it.
        why: What an operator should understand from a match.
    """

    name: str
    regex: re.Pattern[str]
    why: str


# Every pattern below is written so that this module does not match itself. The scan walks `src/`,
# so a pattern that matched its own source would fail the gate the moment it was written — and the
# obvious "fix" would be to stop scanning the harness, which is the one directory most able to hide
# a credential in a fixture. Where a literal was unavoidable it is assembled at use, never written
# out here.
PATTERNS: tuple[SecretPattern, ...] = (
    SecretPattern(
        name="private-key-block",
        regex=re.compile(r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY(?: BLOCK)?-----"),
        why="a private key in PEM or OpenSSH armour; the key itself, not a reference to one",
    ),
    SecretPattern(
        name="age-secret-key",
        regex=re.compile(r"AGE-SECRET-KEY-1[0-9A-Z]{20,}"),
        why="an age identity — the half that decrypts everything this Repository encrypts",
    ),
    SecretPattern(
        name="aws-access-key-id",
        regex=re.compile(r"\b(?:AKIA|ASIA|AGPA|AIDA|AROA)[A-Z0-9]{16}\b"),
        why="an AWS key identifier; its secret half is usually nearby",
    ),
    SecretPattern(
        name="github-token",
        regex=re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36}\b"),
        why="a GitHub token, which grants whatever the account it was minted for can do",
    ),
    SecretPattern(
        name="slack-token",
        regex=re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b"),
        why="a Slack token",
    ),
    SecretPattern(
        name="json-web-token",
        regex=re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
        why="a signed JWT, which is a bearer credential until it expires",
    ),
    SecretPattern(
        name="provider-api-key",
        regex=re.compile(r"\bsk-[A-Za-z0-9]{32,}\b"),
        why="an API key in the `sk-` convention used by several service providers",
    ),
)

_ASSIGNMENT = re.compile(
    r"(?i)(?P<field>pass(?:word|wd|phrase)|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|credential)"
    r"(?![A-Za-z0-9])\s*[:=]\s*(?P<quote>[\"']?)(?P<value>[^\s\"'#`,;()]{12,})(?P=quote)"
)
"""A credential-shaped value assigned to a credential-shaped field name.

**There is no leading boundary at all, and that is deliberate — it is the third attempt.**

1. `\\b` treats `_` as a word character, so `directory_bind_password` did not match: the commonest
   real shape in an Ansible vars file was invisible.
2. `(?<![A-Za-z0-9])` fixed that and broke `bindPassword`, because a camelCase field has a
   lowercase letter immediately before the keyword. Each fixture was written to the same
   assumption as the pattern it tested, so both cuts passed their own tests.

A leading guard can only ever exclude, and every character it excludes is a naming convention
somebody uses. The trailing `(?![A-Za-z0-9])` is kept because it does necessary work — it stops
`tokenizer` and `secretary` — and it costs nothing, since a field name is always followed by `:` or
`=`. What a missing leading guard admits is `mytoken:` and `topsecret:`, which are credential
fields; treating them as false positives was the mistake.

The field name alone proves nothing — this Repository is full of prose about passwords — so the
*value* has to survive `_is_credential_shaped` as well. That predicate is where the false-positive
control lives.
"""

_PLACEHOLDER_MARKERS: tuple[str, ...] = (
    "change-me",
    "change_me",
    "changeme",
    "enc[",
    "example",
    "fixme",
    "placeholder",
    "redact",
    "xxxx",
    "your-",
    "your_",
)
"""Substrings that mark a value as illustrative. A real credential does not announce itself.

**This list must never contain a credential field name.** It once held `password`, `secret`,
`token`, `credential`, and `vault`, and each of those silently exempted every real credential that
happened to contain the word — `s3cr3t-not-a-real-token-abcdef123456` was skipped because it
contains `token`. The predicate is asked "is this value a placeholder?", and the answer was being
read off a word that says nothing about the value and everything about the field it sits in. The
membership test is `in`, so a marker here exempts every value containing it: only substrings that
are implausible inside generated key material belong.

The heavy lifting is not done here at all. It is done by the structural tests below — a value must
be long, mixed, varied, self-contained, and not a reference to something held elsewhere — and those
tests do not care what the value spells.
"""

_TEMPLATE_PREFIXES: tuple[str, ...] = ("$", "%", "{", "<", "!", "&", "*")
"""Leading characters of a reference to a value held elsewhere, which is the correct pattern."""

_DOTENV_METADATA = re.compile(r"^sops_mac=", re.MULTILINE)
"""The dotenv form of SOPS output, which is not a mapping and so never parses to one."""

_SCOPE_NOTE = f"vendored trees not scanned: {list(VENDORED_ROOTS)}"
"""Said in every report. An exclusion nobody is told about is an exclusion nobody can weigh."""


def _is_credential_shaped(value: str) -> bool:
    """Whether an assigned value looks like a credential rather than a reference or an example.

    Args:
        value: The right-hand side of a credential-shaped assignment.

    Returns:
        True when the value is long enough, mixed enough, and self-contained enough to be a real
        secret. Anything that reads as a variable reference, a path, or an illustrative placeholder
        is rejected — a lookup is what the Repository is supposed to contain.
    """
    if not value or value[0] in _TEMPLATE_PREFIXES:
        return False
    if "/" in value or "\\" in value:
        return False
    lowered = value.lower()
    if any(marker in lowered for marker in _PLACEHOLDER_MARKERS):
        return False
    if not any(character.isdigit() for character in value):
        return False
    if not any(character.isalpha() for character in value):
        return False
    return len(set(value)) >= 6


def is_sops_encrypted(text: str) -> bool:
    """Whether a file's contents are SOPS ciphertext.

    A file judged encrypted is skipped by the plaintext scan, so this predicate is a hole in the
    check exactly as wide as it is loose. The marker alone is not enough: this Runbook, and any
    document that shows a sample of encrypted output, contains `ENC[AES256_GCM,` in prose — and the
    first cut of this function skipped every one of them, which is a documented way to smuggle a
    credential past the scan. So the file must also *be* a SOPS document: a mapping carrying a
    `sops` block with a MAC, or the dotenv form's `sops_mac`/`sops_version` pair.

    Args:
        text: The decoded file contents.

    Returns:
        True when the file is SOPS output rather than a document that mentions it.
    """
    if SOPS_CIPHERTEXT_MARKER not in text:
        return False
    if _DOTENV_METADATA.search(text):
        return True
    try:
        document = YAML(typ="safe").load(text)
    except (YAMLError, ValueError):
        return False
    metadata = document.get("sops") if isinstance(document, dict) else None
    return isinstance(metadata, dict) and "mac" in metadata


def scan_text(text: str) -> list[tuple[int, SecretPattern]]:
    """Find every credential-shaped literal in one file's contents.

    Args:
        text: The decoded file contents.

    Returns:
        Pairs of one-based line number and the pattern that matched, in file order. The matched
        text is deliberately not returned: nothing downstream may print it.
    """
    hits: list[tuple[int, SecretPattern]] = []
    for pattern in PATTERNS:
        for match in pattern.regex.finditer(text):
            hits.append((text.count("\n", 0, match.start()) + 1, pattern))
    assignment = SecretPattern(
        name="credential-assignment",
        regex=_ASSIGNMENT,
        why="a credential-shaped value assigned to a credential-shaped field, in plaintext",
    )
    for match in _ASSIGNMENT.finditer(text):
        if _is_credential_shaped(match.group("value")):
            hits.append((text.count("\n", 0, match.start()) + 1, assignment))
    return sorted(hits, key=lambda hit: hit[0])


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def check_encryption_policy(policy: EncryptionPolicy, covered: int) -> CheckResult:
    """The encryption policy is present, parseable, and declares real rules and real recipients.

    Args:
        policy: The parsed `.sops.yaml`.
        covered: How many files in the tree the policy's rules currently match.

    Returns:
        The check result.
    """
    name = "Encryption policy declared"
    location = policy.path.name
    findings: list[Finding] = []
    if not policy.present:
        findings.append(
            Finding(
                defect=defects.UNDECLARED_ENCRYPTION_POLICY,
                subject=location,
                detail="absent, so which paths are encrypted and to whom is nowhere declared",
                location=location,
            )
        )
    elif policy.error:
        findings.append(
            Finding(
                defect=defects.UNDECLARED_ENCRYPTION_POLICY,
                subject=location,
                detail=policy.error,
                location=location,
            )
        )
    elif not policy.rules:
        findings.append(
            Finding(
                defect=defects.UNDECLARED_ENCRYPTION_POLICY,
                subject=location,
                detail="declares an empty 'creation_rules' list, so no path is covered by anything",
                location=location,
            )
        )
    for rule in policy.rules:
        if rule.error:
            findings.append(
                Finding(
                    defect=defects.UNDECLARED_ENCRYPTION_POLICY,
                    subject=f"{location}: {rule.path_regex or 'rule with no path_regex'}",
                    detail=rule.error,
                    location=location,
                )
            )
        # The sentinel is legitimate only while it covers nothing. The moment a file the rule
        # matches exists, the rule cannot encrypt it, and a policy that cannot encrypt what it
        # claims is a policy in name only.
        elif rule.recipients_unset and covered:
            findings.append(
                Finding(
                    defect=defects.UNDECLARED_ENCRYPTION_POLICY,
                    subject=f"{location}: {rule.path_regex}",
                    detail=(
                        f"still names the {RECIPIENT_SENTINEL} sentinel as its recipient while {covered} file(s) "
                        "match it; generate and escrow the control-node age key first — see "
                        "runbooks/l0-physical/repo-secrets.md, Step 1"
                    ),
                    location=location,
                )
            )
    note = ""
    if policy.rules and all(rule.recipients_unset for rule in policy.rules) and not covered:
        note = (
            f"{RECIPIENT_SENTINEL}: no age key has been generated yet, and no file matches any rule, "
            "so nothing is encrypted and nothing needs to be"
        )
    return result(
        name,
        defects.UNDECLARED_ENCRYPTION_POLICY,
        len(policy.rules),
        "declared creation rules",
        findings,
        note=note,
    )


def run_secret_checks(workspace: Workspace, policy: EncryptionPolicy) -> list[CheckResult]:
    """Scan the Repository once, and report the three secret-handling rules from that one walk.

    One walk rather than three: reading every tracked file three times to answer three questions
    about the same bytes is slower for no gain, and the commit hook runs this on every commit.

    Args:
        workspace: The repository under audit.
        policy: The parsed `.sops.yaml`.

    Returns:
        The policy result, the declared-path result, and the plaintext-scan result, in that order.
    """
    files, source = workspace.scannable_files()
    plaintext: list[Finding] = []
    unencrypted: list[Finding] = []
    unreadable: list[str] = []
    scanned = 0
    encrypted = 0
    covered = 0

    for path in files:
        relative = workspace.relative(path)
        text = _read(path)
        if text is None:
            # NOT counted as scanned. A file that could not be decoded was not examined, and a
            # count that includes it is the quiet version of reporting a pass over it.
            unreadable.append(relative)
            continue
        scanned += 1
        rule = policy.rule_for(relative)
        if rule is not None:
            covered += 1
        if is_sops_encrypted(text):
            encrypted += 1
            continue
        if rule is not None:
            unencrypted.append(
                Finding(
                    defect=defects.UNENCRYPTED_DECLARED_PATH,
                    subject=relative,
                    detail=(
                        f"matches the committed rule {rule.path_regex!r} in {policy.path.name} but carries no "
                        "SOPS ciphertext; encrypt it in place with `sops --encrypt --in-place` before committing"
                    ),
                    location=relative,
                )
            )
            continue
        for line, pattern in scan_text(text):
            plaintext.append(
                Finding(
                    defect=defects.PLAINTEXT_SECRET,
                    subject=relative,
                    # The matched text is never included. This detail goes into the CI log of a
                    # public repository, and a log is not a place a credential becomes safe.
                    detail=(
                        f"line {line} matches the {pattern.name} pattern — {pattern.why}. "
                        "Remove it and rotate it: deleting a secret from the working tree does not "
                        "remove it from history"
                    ),
                    location=f"{relative}:{line}",
                )
            )

    note = f"{source}; {encrypted} encrypted, {covered} covered by a creation rule; {_SCOPE_NOTE}"
    if unreadable:
        note += f"; {len(unreadable)} file(s) not decodable as UTF-8 and therefore NOT scanned: {sorted(unreadable)}"
    return [
        check_encryption_policy(policy, covered),
        result(
            "Declared paths are encrypted",
            defects.UNENCRYPTED_DECLARED_PATH,
            covered,
            "files covered by a creation rule",
            unencrypted,
            note="no path matches any creation rule yet" if not covered else "",
        ),
        result(
            "Plaintext secret material",
            defects.PLAINTEXT_SECRET,
            scanned,
            "files scanned",
            plaintext,
            note=note,
        ),
    ]
