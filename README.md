# Lakheslo

Lakheslo is a Flask study assistant for PDF summaries, document-grounded quizzes, and chat. It uses PyMuPDF for page-aware extraction and the official Google GenAI SDK for AI operations.

## Local setup

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `GEMINI_API_KEY` in `.env`, then run:

```powershell
python app.py
```

Open `http://localhost:5000`. The API key remains server-side. The application reports pages with no selectable text rather than silently treating them as successfully extracted.

## Render deployment

Create a Python web service from this repository. Render uses the `Procfile`; configure `GEMINI_API_KEY`, `GEMINI_MODEL`, and a strong `FLASK_SECRET_KEY` as environment variables. Uploaded documents are temporary on Render's filesystem and are held only for the process session.

## Limitations

Text extraction is page-aware and flags image-only pages. Full OCR/vision processing for scanned pages requires adding a vision/OCR pipeline; no fabricated text is generated for those pages. In-memory sessions are intentionally lightweight and are not shared across multiple service instances.
