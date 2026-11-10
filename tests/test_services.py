from pathlib import Path

import fitz

from services.chunking_service import chunk_pages
from services.pdf_service import extract_document


def test_chunk_pages_preserves_page_numbers():
    chunks = chunk_pages([{"page": 1, "text": "alpha"}, {"page": 2, "text": "beta"}], max_chars=6)
    assert [chunk["pages"] for chunk in chunks] == [[1], [2]]


def test_extract_document_tracks_pages(tmp_path: Path):
    path = tmp_path / "sample.pdf"
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "A study page")
    pdf.new_page()
    pdf.save(path)
    pdf.close()
    document = extract_document(path, "sample.pdf", 10)
    assert document["page_count"] == 2
    assert document["extracted_pages"] == 1
    assert document["failed_pages"] == [2]
