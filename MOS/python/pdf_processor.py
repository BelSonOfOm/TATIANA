"""
TATIANA — local PDF extraction (rebuild of the missing PROCESSING.pdf_processor).

Streams a PDF page-by-page so a 1000-page book never has to sit in RAM at once —
which matters a great deal on a 5.9 GB machine. Extraction is CPU-only and costs
no API quota.

Contract expected by the Librarian:
    async for page in processor.stream_extract_pdf(path, start_page=0):
        page["text"], page["page_number"], page["total_pages"]

page_number is 1-indexed; start_page is the number of pages already consumed, so
resuming from a saved checkpoint is exact.
"""

from __future__ import annotations

import asyncio
import os
from typing import AsyncIterator, Dict, Optional


class PDFBackendMissing(RuntimeError):
    pass


def _open_backend():
    """Prefer pdfplumber (better layout fidelity); fall back to pypdf."""
    try:
        import pdfplumber  # noqa: F401
        return "pdfplumber"
    except ImportError:
        pass
    try:
        import pypdf  # noqa: F401
        return "pypdf"
    except ImportError:
        raise PDFBackendMissing(
            "No PDF backend available. Install one on Python 3.11:\n"
            "    python -m pip install pdfplumber")


class LocalProcessor:
    """CPU-only, streaming PDF text extraction."""

    def __init__(self, backend: Optional[str] = None):
        self.backend = backend or _open_backend()

    async def stream_extract_pdf(self, path: str,
                                 start_page: int = 0) -> AsyncIterator[Dict]:
        """Yield one dict per page, beginning AFTER `start_page` pages.

        Pages that yield no extractable text (scans/images) are still emitted with
        empty text rather than skipped, so page numbering stays truthful and the
        caller can see that a page produced nothing instead of silently losing it.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"PDF not found: {path}")

        if self.backend == "pdfplumber":
            import pdfplumber
            with pdfplumber.open(path) as pdf:
                total = len(pdf.pages)
                for idx in range(start_page, total):
                    text = pdf.pages[idx].extract_text() or ""
                    yield {"text": text, "page_number": idx + 1, "total_pages": total}
                    await asyncio.sleep(0)  # stay cooperative for the event loop
        else:
            from pypdf import PdfReader
            reader = PdfReader(path)
            total = len(reader.pages)
            for idx in range(start_page, total):
                text = reader.pages[idx].extract_text() or ""
                yield {"text": text, "page_number": idx + 1, "total_pages": total}
                await asyncio.sleep(0)

    async def extract_front_matter(self, path: str, max_chars: int = 1500,
                                   max_pages: int = 3) -> str:
        """First few pages only — enough to classify a document cheaply."""
        buf = []
        n = 0
        async for page in self.stream_extract_pdf(path):
            buf.append(page["text"])
            n += 1
            if sum(len(b) for b in buf) > max_chars or n >= max_pages:
                break
        return "\n".join(buf)


if __name__ == "__main__":
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), "..", "..", "DOCS", "FIRST DRAFT.pdf")

    async def main():
        proc = LocalProcessor()
        print("backend:", proc.backend)
        target_abs = os.path.abspath(target)
        print("file:", target_abs)
        if not os.path.exists(target_abs):
            print("(file not found; skipping extraction demo)")
            return
        pages = 0
        chars = 0
        async for page in proc.stream_extract_pdf(target_abs):
            pages += 1
            chars += len(page["text"])
            if pages == 1:
                # Windows consoles default to cp1252 and choke on characters like
                # the non-breaking hyphen U+2011 that are common in typeset PDFs.
                preview = page["text"][:120].encode("ascii", "replace").decode("ascii")
                print(f"page 1/{page['total_pages']} first 120 chars: {preview!r}")
        print(f"streamed {pages} pages, {chars} chars total")

    asyncio.run(main())
