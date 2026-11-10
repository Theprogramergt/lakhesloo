from __future__ import annotations

import json
import os
import threading
import uuid
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

load_dotenv()

from config import Config
from services.chat_service import answer_question
from services.gemini_service import GeminiService, GeminiServiceError
from services.pdf_service import extract_document
from services.quiz_service import generate_quiz
from services.summary_service import generate_summary


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    documents: dict[str, dict] = {}
    lock = threading.Lock()
    gemini = GeminiService(
        api_key=app.config["GEMINI_API_KEY"],
        model=app.config["GEMINI_MODEL"],
    )

    @app.errorhandler(413)
    def request_too_large(_error):
        return jsonify(error="The PDF exceeds the configured size limit."), 413

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/api/documents")
    def upload_document():
        uploaded = request.files.get("file")
        if not uploaded or not uploaded.filename:
            return jsonify(error="Choose a PDF file to upload."), 400
        if not uploaded.filename.lower().endswith(".pdf"):
            return jsonify(error="Only PDF files are supported."), 400

        document_id = uuid.uuid4().hex
        filename = secure_filename(uploaded.filename)
        path = Path(app.config["UPLOAD_FOLDER"]) / f"{document_id}.pdf"
        uploaded.save(path)
        if path.stat().st_size > app.config["MAX_CONTENT_LENGTH"]:
            path.unlink(missing_ok=True)
            return jsonify(error="The PDF exceeds the configured size limit."), 413
        try:
            document = extract_document(path, filename, app.config["MAX_PAGES"])
        except ValueError as exc:
            path.unlink(missing_ok=True)
            return jsonify(error=str(exc)), 422
        document.update({"id": document_id, "path": str(path), "chat_history": []})
        with lock:
            documents[document_id] = document
        return jsonify(
            id=document_id,
            filename=filename,
            page_count=document["page_count"],
            extracted_pages=document["extracted_pages"],
            failed_pages=document["failed_pages"],
            warnings=document["warnings"],
        )

    def get_document(document_id: str) -> dict:
        document = documents.get(document_id)
        if document is None:
            raise KeyError("Document session not found.")
        return document

    @app.post("/api/documents/<document_id>/summary")
    def summary(document_id: str):
        try:
            document = get_document(document_id)
            payload = request.get_json(silent=True) or {}
            style = payload.get("style", "comprehensive")
            if style not in {"comprehensive", "quick"}:
                return jsonify(error="Summary style must be comprehensive or quick."), 400
            result = generate_summary(document, style, gemini)
            return jsonify(result)
        except KeyError as exc:
            return jsonify(error=str(exc)), 404
        except GeminiServiceError as exc:
            return jsonify(error=str(exc)), 503

    @app.post("/api/documents/<document_id>/quiz")
    def quiz(document_id: str):
        try:
            document = get_document(document_id)
            payload = request.get_json(silent=True) or {}
            difficulty = payload.get("difficulty", "medium")
            try:
                count = max(1, min(int(payload.get("count", 5)), 15))
            except (TypeError, ValueError):
                return jsonify(error="Question count must be a number."), 400
            result = generate_quiz(document, difficulty, count, gemini)
            return jsonify(result)
        except KeyError as exc:
            return jsonify(error=str(exc)), 404
        except (GeminiServiceError, ValueError) as exc:
            return jsonify(error=str(exc)), 503

    @app.post("/api/documents/<document_id>/chat")
    def chat(document_id: str):
        try:
            document = get_document(document_id)
            payload = request.get_json(silent=True) or {}
            question = str(payload.get("question", "")).strip()
            if not question or len(question) > 4000:
                return jsonify(error="Enter a question of 1–4000 characters."), 400
            result = answer_question(document, question, gemini)
            document["chat_history"].extend(
                [{"role": "user", "content": question}, {"role": "model", "content": result["answer"]}]
            )
            return jsonify(result)
        except KeyError as exc:
            return jsonify(error=str(exc)), 404
        except GeminiServiceError as exc:
            return jsonify(error=str(exc)), 503

    @app.get("/uploads/<path:name>")
    def uploads(name: str):
        return send_from_directory(app.config["UPLOAD_FOLDER"], name)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
