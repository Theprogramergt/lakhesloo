from __future__ import annotations

from services.gemini_service import GeminiService


def generate_quiz(document: dict, difficulty: str, count: int, gemini: GeminiService) -> dict:
    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError("Difficulty must be easy, medium, or hard.")
    # Keep the request within free-tier context limits while representing the
    # beginning, middle, and end of every extracted chunk.
    excerpts = []
    for chunk in document["chunks"]:
        text = chunk["text"]
        excerpt_size = max(1200, 42000 // max(1, len(document["chunks"])))
        excerpts.append(text[:excerpt_size])
    prompt = f"""Create exactly {count} {difficulty} multiple-choice questions from the PDF content below.
Return JSON only with this shape:
{{"questions":[{{"question":"...","options":["A","B","C","D"],"answer":0,"explanation":"...","pages":[1]}}]}}
The answer is a zero-based option index. Use document facts only.
For every mathematical expression, use LaTeX enclosed in \\(...\\) for inline math or \\[...\\] for display math.
Never return bare LaTeX commands, and never use dollar-sign math delimiters.
Document:
{chr(10).join(excerpts)}"""
    result = gemini.generate(prompt, response_json=True)
    questions = result.get("questions") if isinstance(result, dict) else None
    if not isinstance(questions, list) or not questions:
        raise ValueError("Gemini returned an invalid quiz.")
    for question in questions:
        if not isinstance(question, dict) or not isinstance(question.get("options"), list):
            raise ValueError("Gemini returned an invalid quiz question.")
        if len(question["options"]) < 2 or not isinstance(question.get("answer"), int):
            raise ValueError("Gemini returned incomplete quiz data.")
    return {"difficulty": difficulty, "questions": questions[:count]}
