from __future__ import annotations

from pathlib import Path

import fitz

from services.chunking_service import chunk_pages


def extract_document(path: Path, filename: str, max_pages: int) -> dict:
    try:
        pdf = fitz.open(path)
    except Exception as exc:
        raise ValueError("The uploaded file is not a readable PDF.") from exc
    if pdf.page_count == 0:
        raise ValueError("The PDF has no pages.")
    if pdf.page_count > max_pages:
        raise ValueError(f"This PDF has {pdf.page_count} pages; the limit is {max_pages}.")

    pages = []
    failed_pages = []
    warnings = []
    for number, page in enumerate(pdf, start=1):
        try:
            text = page.get_text("text").strip()
        except Exception:
            text = ""
        if not text:
            failed_pages.append(number)
            text = "[No selectable text extracted from this page. It may be scanned or image-based.]"
        pages.append({"page": number, "text": text})
    if failed_pages:
        warnings.append(
            f"{len(failed_pages)} page(s) had no selectable text. Image-only mathematical content may need OCR."
        )
    return {
        "filename": filename,
        "page_count": pdf.page_count,
        "extracted_pages": pdf.page_count - len(failed_pages),
        "failed_pages": failed_pages,
        "warnings": warnings,
        "pages": pages,
        "chunks": chunk_pages(pages),
    }
