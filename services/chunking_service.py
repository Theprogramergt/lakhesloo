from __future__ import annotations


def chunk_pages(pages: list[dict], max_chars: int = 12000) -> list[dict]:
    chunks = []
    current: list[str] = []
    current_pages: list[int] = []
    size = 0
    for page in pages:
        text = page["text"]
        if current and size + len(text) > max_chars:
            chunks.append({"pages": current_pages, "text": "\n\n".join(current)})
            current, current_pages, size = [], [], 0
        current.append(f"[Page {page['page']}]\n{text}")
        current_pages.append(page["page"])
        size += len(text)
    if current:
        chunks.append({"pages": current_pages, "text": "\n\n".join(current)})
    return chunks
