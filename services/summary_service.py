from __future__ import annotations

from services.gemini_service import GeminiService


def generate_summary(document: dict, style: str, gemini: GeminiService) -> dict:
    cache_key = f"summary_{style}"
    if cache_key in document:
        return document[cache_key]
    detail = (
        "Be comprehensive: cover every section, definitions, formulas, theorems, methods, examples, and conclusions."
        if style == "comprehensive"
        else "Be concise: retain the essential ideas, definitions, and most important formulas."
    )
    partials = []
    for chunk in document["chunks"]:
        partials.append(
            gemini.generate(
                f"""You are summarizing part of a study PDF. Use LaTeX for mathematics.
{detail}
Preserve page references from the source. Do not invent content.
Source pages {chunk['pages']}:
{chunk['text']}"""
            )
        )
    combined = "\n\n".join(f"Section from pages {c['pages']}:\n{p}" for c, p in zip(document["chunks"], partials))
    final = gemini.generate(
        f"""Create the final {style} study summary from ALL partial summaries below.
Organize it with Markdown headings and bullet lists. Use LaTeX delimiters: \\(...\\) inline and \\[...\\] for display equations.
Keep page references, reconcile overlap, and do not claim coverage beyond the supplied material.
Partial summaries:
{combined}"""
    )
    result = {"style": style, "content": final, "covered_pages": document["page_count"], "warnings": document["warnings"]}
    document[cache_key] = result
    return result
