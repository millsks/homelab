"""The committed encryption policy: which paths are encrypted, and to which recipients.

`.sops.yaml` is the Automation half of `PROC-REPO-SECRETS`, and it is the reason the rule
"which paths are encrypted" is answerable by reading the Repository rather than by asking the
operator what they remember. This module turns it into something the harness can check against
the filesystem, so the policy is enforced rather than merely stated.

**The recipient sentinel.** A recipient is an age *public* key, and no key exists yet: generating
one here would put the only copy of its private half on one machine, which is precisely the escrow
failure AD-24 names. So the shipped policy carries `AGE-RECIPIENT-UNSET`, on the same principle as
`TEMPLATE-UNFILLED` in `runbooks/TEMPLATE.md` — a sentinel that is grep-visible and structurally
invalid, rather than a plausible-looking placeholder that could be mistaken for a real key. Step 1
of `runbooks/l0-physical/repo-secrets.md` replaces it, and the harness reports the sentinel as a
defect the moment any file the policy covers actually exists.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

RECIPIENT_SENTINEL = "AGE-RECIPIENT-UNSET"
"""What the shipped policy names instead of an age public key nobody has generated yet."""

POLICY_FILENAME = ".sops.yaml"
"""Where the policy lives. SOPS looks for this name at the Repository root."""


@dataclass(frozen=True, slots=True)
class CreationRule:
    """One `creation_rules` entry: a path pattern and the recipients it encrypts to.

    Attributes:
        path_regex: The pattern SOPS matches a path against, exactly as written.
        recipients: The age recipients declared for matching paths.
        error: Why `path_regex` could not be compiled, if it could not.
    """

    path_regex: str
    recipients: tuple[str, ...]
    error: str = ""

    @property
    def recipients_unset(self) -> bool:
        """Whether the rule still names the sentinel rather than a real recipient.

        Returns:
            True when no recipient is declared, or every declared recipient is the sentinel.
        """
        return not self.recipients or all(name == RECIPIENT_SENTINEL for name in self.recipients)

    def matches(self, relative: str) -> bool:
        """Whether a repository-relative path falls under this rule.

        SOPS matches `path_regex` as an unanchored search, so this does too.

        Args:
            relative: A POSIX-style repository-relative path.

        Returns:
            True when the rule covers the path. A rule that could not be compiled matches
            nothing — and is reported separately, never silently treated as covering everything.
        """
        if self.error:
            return False
        return re.search(self.path_regex, relative) is not None


@dataclass(frozen=True, slots=True)
class EncryptionPolicy:
    """`.sops.yaml`, parsed.

    Attributes:
        path: Where the policy was looked for.
        present: Whether the file exists at all.
        rules: The declared creation rules, in file order.
        error: Why the file could not be read or parsed, if it could not.
    """

    path: Path
    present: bool
    rules: tuple[CreationRule, ...] = ()
    error: str = ""

    def rule_for(self, relative: str) -> CreationRule | None:
        """The first rule covering a path, as SOPS itself resolves it.

        Args:
            relative: A POSIX-style repository-relative path.

        Returns:
            The first matching rule, or `None` when no rule covers the path.
        """
        for rule in self.rules:
            if rule.matches(relative):
                return rule
        return None


def _recipients_of(block: object) -> tuple[str, ...]:
    """Read the `age` recipients of one creation rule.

    SOPS accepts either a comma-separated string or a list, so both are read here rather than one
    being assumed and the other silently yielding zero recipients.

    Args:
        block: The mapping for a single creation rule.

    Returns:
        Every recipient named, stripped, in declaration order.
    """
    if not isinstance(block, dict):
        return ()
    declared = block.get("age")
    if isinstance(declared, str):
        return tuple(name.strip() for name in declared.split(",") if name.strip())
    if isinstance(declared, list):
        return tuple(str(name).strip() for name in declared if str(name).strip())
    return ()


def load_policy(path: Path) -> EncryptionPolicy:
    """Parse the encryption policy.

    A missing, unreadable, or unparseable policy is reported as such rather than as an empty one:
    an empty policy covers no path, so treating a broken file as empty would turn a defect into a
    silent pass — which is the failure mode this repository keeps finding in its own gates.

    Args:
        path: The `.sops.yaml` to read.

    Returns:
        The parsed policy.
    """
    if not path.is_file():
        return EncryptionPolicy(path=path, present=False)
    try:
        document = YAML(typ="safe").load(path.read_text(encoding="utf-8"))
    except (YAMLError, OSError, UnicodeDecodeError) as error:
        return EncryptionPolicy(path=path, present=True, error=f"could not be parsed as YAML: {error}")
    if not isinstance(document, dict):
        return EncryptionPolicy(path=path, present=True, error="does not parse to a mapping")
    declared = document.get("creation_rules")
    if not isinstance(declared, list):
        return EncryptionPolicy(path=path, present=True, error="declares no 'creation_rules' list")

    rules: list[CreationRule] = []
    for block in declared:
        if not isinstance(block, dict):
            rules.append(CreationRule(path_regex="", recipients=(), error="creation rule is not a mapping"))
            continue
        pattern = str(block.get("path_regex", "")).strip()
        rule_error = ""
        if not pattern:
            rule_error = "creation rule names no 'path_regex', so it covers nothing"
        else:
            try:
                re.compile(pattern)
            except re.error as compile_error:
                rule_error = f"path_regex {pattern!r} is not a usable regular expression: {compile_error}"
        rules.append(CreationRule(path_regex=pattern, recipients=_recipients_of(block), error=rule_error))
    return EncryptionPolicy(path=path, present=True, rules=tuple(rules))
