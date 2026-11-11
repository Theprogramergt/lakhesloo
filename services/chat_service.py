from __future__ import annotations

import re

from services.gemini_service import GeminiService


def _relevant_chunks(document: dict, question: str, limit: int = 4) -> list[dict]:
    terms = set(re.findall(r"\w+", question.lower()))
    scored = []
    for chunk in document["chunks"]:
        words = set(re.findall(r"\w+", chunk["text"].lower()))
        scored.append((len(terms & words), chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [chunk for score, chunk in scored[:limit] if score > 0] or document["chunks"][:limit]


def answer_question(document: dict, question: str, gemini: GeminiService) -> dict:
    chunks = _relevant_chunks(document, question)
    history = document["chat_history"][-6:]
    prompt = f"""Answer the student's question using only the supplied PDF excerpts.
If the answer is not present, say so clearly. Cite page numbers when possible.
Give step-by-step mathematical reasoning. Put every mathematical expression in
LaTeX using \\(...\\) for inline math or \\[...\\] for display math. Never return
bare LaTeX commands or dollar-sign math delimiters.
Conversation history: {history}
Question: {question}
PDF excerpts:
{chr(10).join(chunk['text'] for chunk in chunks)}"""
    return {"answer": gemini.generate(prompt), "pages": sorted({p for c in chunks for p in c["pages"]})}
