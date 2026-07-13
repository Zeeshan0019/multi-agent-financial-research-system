
from __future__ import annotations
import re
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List

import fitz

logger = logging.getLogger("pdf_parser")
logging.basicConfig(level=logging.INFO)

@dataclass
class PageText:
    page_number: int        
    text: str
    char_count: int = 0

    def __post_init__(self):
        self.char_count = len(self.text)


@dataclass
class ParsedDocument:
    file_name: str
    page_count: int
    pages: List[PageText]
    total_chars: int
    likely_scanned: bool     


class PDFParser:
    MIN_AVG_CHARS_PER_PAGE = 50

    def parse(self, file_path: str) -> ParsedDocument:
        file_name = Path(file_path).name
        pages = self._extract_pages(file_path)

        total_chars = sum(p.char_count for p in pages)
        avg_chars_per_page = total_chars / max(len(pages), 1)
        likely_scanned = avg_chars_per_page < self.MIN_AVG_CHARS_PER_PAGE

        if likely_scanned:
            logger.warning(
                "%s looks like a scanned PDF (avg %.1f chars/page). "
                "OCR is not implemented in this parser yet.",
                file_name, avg_chars_per_page,
            )

        return ParsedDocument(
            file_name=file_name,
            page_count=len(pages),
            pages=pages,
            total_chars=total_chars,
            likely_scanned=likely_scanned,
        )

    def _extract_pages(self, file_path: str) -> List[PageText]:
        pages: List[PageText] = []
        with fitz.open(file_path) as pdf:
            for i, page in enumerate(pdf, start=1):
                raw_text = page.get_text("text")
                cleaned = self._clean_text(raw_text)
                pages.append(PageText(page_number=i, text=cleaned))
        return pages

    @staticmethod
    def _clean_text(text: str) -> str:
        """Collapse excess whitespace/form-feeds left over from PDF extraction."""
        text = text.replace("\x0c", " ")           # form-feed page breaks
        text = re.sub(r"[ \t]+", " ", text)         # collapse runs of spaces/tabs
        text = re.sub(r"\n{3,}", "\n\n", text)      # collapse excess blank lines
        return text.strip()

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pdf_parser.py <path_to_pdf>")
        sys.exit(1)

    parser = PDFParser()
    parsed = parser.parse(sys.argv[1])

    print(f"\nFile: {parsed.file_name}")
    print(f"Pages: {parsed.page_count}")
    print(f"Total characters extracted: {parsed.total_chars}")
    print(f"Likely scanned (no text layer): {parsed.likely_scanned}")

    print("\n--- Page 1 preview ---")
    print(parsed.pages[0].text[:500], "...")

    print("\n--- Per-page character counts (first 10 pages) ---")
    for p in parsed.pages[:10]:
        print(f"  Page {p.page_number}: {p.char_count} chars")

