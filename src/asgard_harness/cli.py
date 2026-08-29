"""Command-line entry point for the convergence harness.

Output goes through `structlog`, so the same run is readable at a terminal and parseable by a log
aggregator — the scheduled drift run in particular has to be *recorded*, not merely watched.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import structlog

from asgard_harness.audit import run_audit, run_convergence, run_drift
from asgard_harness.findings import AuditReport
from asgard_harness.selfcheck import run_self_check
from asgard_harness.workspace import Workspace

COMMANDS = ("audit", "selfcheck", "drift", "converge", "all")

GATE_COMMANDS = ("audit", "selfcheck")
"""What `all` runs: the pure readers only.

`drift` and `converge` shell out to real tools against managed systems, so they are scheduled
rather than folded into a default run. `all` is what a developer types; it must never reach
production because someone forgot which subcommand was which.
"""


def configure_logging(*, as_json: bool) -> None:
    """Configure structlog for one run.

    Args:
        as_json: Render events as JSON rather than as key-value console output.
    """
    renderer: Any = structlog.processors.JSONRenderer() if as_json else structlog.dev.ConsoleRenderer(colors=False)
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(20),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )


def emit(report: AuditReport, command: str, *, as_json: bool) -> None:
    """Write a report to stdout.

    Args:
        report: The report to render.
        command: Which command produced it.
        as_json: Emit the whole report as one JSON event rather than line by line.
    """
    log = structlog.get_logger("asgard_harness")
    if as_json:
        log.info("report", command=command, **report.as_dict())
        return
    for line in report.render().splitlines():
        if line:
            log.info(line, command=command)
    if report.exit_code:
        log.error("defects found", command=command, count=len(report.findings))


def record(report: AuditReport, command: str, destination: Path) -> None:
    """Write a machine-readable record of a run.

    AD-23 requires a non-empty check-mode diff to be *recorded*, not only to exit non-zero.

    Args:
        report: The report to record.
        command: Which command produced it.
        destination: Where to write the JSON record.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {"command": command, **report.as_dict()}
    destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser.

    Returns:
        The parser.
    """
    parser = argparse.ArgumentParser(
        prog="asgard-harness",
        description="Make the repository's own definitions executable, and prove the checks can fail.",
    )
    parser.add_argument("command", choices=COMMANDS, nargs="?", default="all", help="what to run")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root to audit")
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    parser.add_argument("--record", type=Path, default=None, help="write a JSON record of the run to this path")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the harness.

    Args:
        argv: Command-line arguments, defaulting to `sys.argv[1:]`.

    Returns:
        `0` when everything checked passes, `1` when any check found a defect.
    """
    args = build_parser().parse_args(argv)
    configure_logging(as_json=bool(args.json))
    workspace = Workspace(root=Path(args.root).resolve())

    runners = {
        "audit": run_audit,
        "drift": run_drift,
        "converge": run_convergence,
        "selfcheck": run_self_check,
    }
    commands = list(GATE_COMMANDS) if args.command == "all" else [args.command]

    exit_code = 0
    for command in commands:
        report = runners[command](workspace)
        emit(report, command, as_json=bool(args.json))
        if args.record is not None:
            target = args.record if len(commands) == 1 else args.record.with_name(f"{command}-{args.record.name}")
            record(report, command, target)
        exit_code = exit_code or report.exit_code
    return exit_code


if __name__ == "__main__":  # pragma: no cover - exercised through __main__.py
    sys.exit(main())
