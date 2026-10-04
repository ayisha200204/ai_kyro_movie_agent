from __future__ import annotations

import re
from typing import Any

from google import genai
from google.genai import types

from .config import settings


class GeminiService:
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured. Add it to .env."
            )

        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

    def embed(
        self,
        texts: list[str],
        task_type: str = "RETRIEVAL_DOCUMENT",
    ) -> list[list[float]]:
        response = self.client.models.embed_content(
            model=settings.embedding_model,
            contents=texts,
            config=types.EmbedContentConfig(
                task_type=task_type
            ),
        )

        return [
            list(item.values)
            for item in response.embeddings
        ]

    def generate(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2
            ),
        )

        return response.text or ""

    def route(
        self,
        user_query: str,
        movie_titles: list[str],
    ) -> dict[str, Any]:
        """
        Deterministic routing.

        Routing does not require Gemini because we can identify:
        - email actions
        - email addresses
        - explicitly mentioned movie titles
        - genuinely generic questions

        This saves one Gemini generation request per user query.
        """
        return self.fallback_route(
            user_query,
            movie_titles,
        )

    @staticmethod
    def fallback_route(
        user_query: str,
        movie_titles: list[str],
    ) -> dict[str, Any]:
        lower = user_query.lower()

        # ---------------------------------------------------------
        # 1. Detect email/action request
        # ---------------------------------------------------------
        action_words = [
            "email",
            "e-mail",
            "send",
            "share",
        ]

        is_action = any(
            word in lower
            for word in action_words
        )

        # ---------------------------------------------------------
        # 2. Detect explicitly mentioned movie
        # ---------------------------------------------------------
        movie = next(
            (
                title
                for title in movie_titles
                if title.lower() in lower
            ),
            None,
        )

        # ---------------------------------------------------------
        # 3. Extract recipient email
        # ---------------------------------------------------------
        match = re.search(
            r"[\w.+-]+@[\w-]+\.[\w.-]+",
            user_query,
        )

        recipient = (
            match.group(0)
            if match
            else None
        )

        # ---------------------------------------------------------
        # 4. Email request without recipient
        # ---------------------------------------------------------
        if is_action and not recipient:
            return {
                "intent": "clarification",
                "movie_title": movie,
                "recipient_email": None,
                "clarification_needed": True,
                "reason": "Recipient email is missing.",
            }

        # ---------------------------------------------------------
        # 5. Detect genuinely generic questions
        # ---------------------------------------------------------
        generic_patterns = [
            "what happens in the movie",
            "what happens in this movie",
            "tell me about the movie",
            "tell me about this movie",
            "give me a summary",
            "give me the summary",
            "summarize the movie",
            "summarize this movie",
            "what is the movie about",
            "what's the movie about",
        ]

        is_generic = any(
            phrase in lower
            for phrase in generic_patterns
        )

        # Ask for a movie only when the request
        # is genuinely generic.
        if is_generic and not movie:
            return {
                "intent": "clarification",
                "movie_title": None,
                "recipient_email": recipient,
                "clarification_needed": True,
                "reason": "Movie title is ambiguous or missing.",
            }

        # ---------------------------------------------------------
        # 6. Everything else can be handled by RAG
        # ---------------------------------------------------------
        return {
            "intent": (
                "email_action"
                if is_action
                else "informational"
            ),
            "movie_title": movie,
            "recipient_email": recipient,
            "clarification_needed": False,
            "reason": "",
        }

    def answer(
        self,
        question: str,
        contexts: list[dict[str, Any]],
    ) -> str:
        """
        Generate a grounded answer from retrieved subtitle chunks.

        This is the main Gemini generation call.
        """

        context_text = "\n\n".join(
            (
                f"SOURCE {i}: "
                f"{c['movie_title']} | "
                f"{c['start']} -> {c['end']}\n"
                f"{c['dialogue']}"
            )
            for i, c in enumerate(contexts, 1)
        )

        prompt = f"""You are a grounded movie subtitle assistant.

Answer the user's question ONLY from the supplied subtitle sources.

Do not use outside movie knowledge.

If the sources do not contain enough evidence,
say that clearly.

Citations are mandatory.

Cite factual statements using this exact format:

[Source N: Movie Title, start -> end]

Do not invent dialogue, movie titles, or timestamps.

Keep the answer concise and directly answer the user's question.

USER QUESTION:
{question}

SUBTITLE SOURCES:
{context_text}
"""

        return self.generate(prompt)