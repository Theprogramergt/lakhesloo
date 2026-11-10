from __future__ import annotations

import json
from typing import Any


class GeminiServiceError(RuntimeError):
    """A safe, user-facing Gemini service failure."""


class GeminiService:
    def __init__(self, api_key: str, model: str):
        self.model = model
        self._client = None
        if api_key:
            try:
                from google import genai

                self._client = genai.Client(api_key=api_key)
            except Exception as exc:
                raise GeminiServiceError("Gemini could not be initialized. Check your API configuration.") from exc

    def generate(self, prompt: str, *, response_json: bool = False) -> str | dict[str, Any]:
        if self._client is None:
            raise GeminiServiceError("Gemini is not configured. Set GEMINI_API_KEY before using AI features.")
        try:
            config = {"temperature": 0.2}
            if response_json:
                config["response_mime_type"] = "application/json"
            response = self._client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )
            text = (response.text or "").strip()
            if not text:
                raise GeminiServiceError("Gemini returned an empty response.")
            return json.loads(text) if response_json else text
        except GeminiServiceError:
            raise
        except Exception as exc:
            message = str(exc).lower()
            if "quota" in message or "rate" in message or "429" in message:
                raise GeminiServiceError("Gemini quota or rate limit reached. Please try again later.") from exc
            raise GeminiServiceError("Gemini could not process the request. Please try again.") from exc
