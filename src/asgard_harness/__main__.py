"""Allow `python -m asgard_harness`."""

from __future__ import annotations

import sys

from asgard_harness.cli import main

if __name__ == "__main__":
    sys.exit(main())
