"""
TATIANA — console encoding fix.

Windows consoles default to cp1252, which cannot encode the characters this
project produces constantly: Delta, rho, omega, subscripts, non-breaking hyphens
from typeset PDFs. Printing any of them raises UnicodeEncodeError and kills the
process — an infuriating way to lose a long-running ingestion.

Call setup() at the top of any entry point that prints mathematics.
"""

from __future__ import annotations

import sys


def setup() -> None:
    """Force stdout/stderr to UTF-8 where the platform allows it."""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                # Redirected/closed stream: fall through to safe() at call sites.
                pass


def safe(text: str) -> str:
    """Last-resort: make a string printable on any console.

    Use when the destination encoding is unknown or setup() could not be applied.
    """
    enc = getattr(sys.stdout, "encoding", None) or "ascii"
    try:
        text.encode(enc)
        return text
    except (UnicodeEncodeError, LookupError):
        return text.encode(enc, "replace").decode(enc, "replace")
