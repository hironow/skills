"""Console output shared by the tooling scripts."""

from __future__ import annotations

import io
import sys


def utf8_stdout() -> None:
    """Write stdout as UTF-8 whatever the console's code page.

    The scripts print ✅ and ❌, which cp932 (a Japanese Windows console)
    cannot encode: without this a clean audit dies with UnicodeEncodeError.
    """
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
