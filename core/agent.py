from __future__ import annotations

import asyncio
import os
import re
from pathlib import Path
from typing import Any

from mcp import Client, StdioServerParameters

from .llm import GeminiService
from .vector_store import MovieVectorStore


class MovieAgent:
    def __init__(self) -> None:
        self.llm = GeminiService()
        self.store = MovieVectorStore()

    def _extract_movie_from_route(
        self,
        route: dict[str, Any],
    ) -> str | None:
        title = route.get("movie_title")

        if title and title in self.store.movie_titles():
            return title

        return None

    def handle(
        self,
        user_query: str,
    ) -> dict[str, Any]:

        # ---------------------------------------------------------
        # 1. Get indexed movie titles
        # ---------------------------------------------------------
        titles = self.store.movie_titles()

        if not titles:
            return {
                "type": "error",
                "message": (
                    "No subtitle index found. "
                    "Run: python -m core.ingest"
                ),
            }

        # ---------------------------------------------------------
        # 2. Determine intent using deterministic routing
        # ---------------------------------------------------------
        route = self.llm.route(
            user_query,
            titles,
        )

        # ---------------------------------------------------------
        # 3. Handle clarification
        # ---------------------------------------------------------
        if (
            route.get("intent") == "clarification"
            or route.get("clarification_needed")
        ):
            return {
                "type": "clarification",
                "message": self._clarification_message(
                    route,
                    titles,
                ),
                "route": route,
            }

        # ---------------------------------------------------------
        # 4. Identify movie if explicitly mentioned
        # ---------------------------------------------------------
        movie_title = self._extract_movie_from_route(
            route
        )

        # ---------------------------------------------------------
        # 5. Retrieve relevant subtitle chunks
        #
        # If movie_title is None, the vector store searches
        # across all indexed movies.
        # ---------------------------------------------------------
        contexts = self.store.query(
            user_query,
            movie_title=movie_title,
        )

        if not contexts:
            return {
                "type": "answer",
                "answer": (
                    "I could not find relevant dialogue "
                    "in the indexed subtitles."
                ),
                "route": route,
            }

        # ---------------------------------------------------------
        # 6. Generate grounded RAG answer
        #
        # This is the only Gemini generation call for the request.
        # ---------------------------------------------------------
        answer = self.llm.answer(
            user_query,
            contexts,
        )

        # ---------------------------------------------------------
        # 7. Handle email action
        # ---------------------------------------------------------
        if route.get("intent") == "email_action":

            recipient = route.get(
                "recipient_email"
            )

            if (
                not recipient
                or not re.fullmatch(
                    r"[^@\s]+@[^@\s]+\.[^@\s]+",
                    recipient,
                )
            ):
                return {
                    "type": "clarification",
                    "message": (
                        "Please provide a valid "
                        "recipient email address."
                    ),
                    "route": route,
                }

            # Create email directly from the grounded answer.
            # No additional Gemini call is required.
            email_body = self._create_email_body(
                answer
            )

            result = asyncio.run(
                self._send_email_via_mcp(
                    recipient,
                    "Movie Assistant – Requested Scene/Dialogue",
                    email_body,
                )
            )

            return {
                "type": "email",
                "answer": answer,
                "email_body": email_body,
                "email_result": result,
                "route": route,
                "sources": contexts,
            }

        # ---------------------------------------------------------
        # 8. Normal informational response
        # ---------------------------------------------------------
        return {
            "type": "answer",
            "answer": answer,
            "sources": contexts,
            "route": route,
        }

    @staticmethod
    def _clarification_message(
        route: dict[str, Any],
        titles: list[str],
    ) -> str:

        reason = str(
            route.get("reason", "")
        ).lower()

        if "recipient" in reason:
            return (
                "Which email address should I "
                "send it to?"
            )

        if (
            "movie" in reason
            or "ambiguous" in reason
        ):
            return (
                "Which movie do you mean? "
                "Available indexed movies: "
                + ", ".join(titles)
            )

        return (
            "Could you clarify the movie, scene, "
            "or recipient so I do not guess?"
        )

    @staticmethod
    def _create_email_body(
        answer: str,
    ) -> str:
        """
        Build the email directly from the grounded
        RAG answer.

        No Gemini call is required here.
        """

        return f"""Hello,

Here is the requested movie information:

{answer}

Best regards,
Movie Intelligence & Follow-up Assistant
"""

    async def _send_email_via_mcp(
        self,
        recipient: str,
        subject: str,
        body: str,
    ) -> str:

        # ---------------------------------------------------------
        # Locate MCP email server
        # ---------------------------------------------------------
        server_file = (
            Path(__file__).resolve().parents[1]
            / "mcp_server"
            / "email_server.py"
        )

        # ---------------------------------------------------------
        # Pass current environment to MCP server
        # ---------------------------------------------------------
        env = dict(os.environ)

        server = StdioServerParameters(
            command="python",
            args=[str(server_file)],
            env=env,
        )

        # ---------------------------------------------------------
        # Connect to MCP server
        # ---------------------------------------------------------
        async with Client(server) as client:

            result = await client.call_tool(
                "send_email",
                {
                    "recipient": recipient,
                    "subject": subject,
                    "body": body,
                },
            )

            # -----------------------------------------------------
            # MCP reported an error
            # -----------------------------------------------------
            if result.is_error:

                details = []

                for item in result.content or []:
                    details.append(
                        getattr(
                            item,
                            "text",
                            str(item),
                        )
                    )

                error_message = (
                    "MCP email tool reported an error."
                )

                if details:
                    error_message += (
                        " Details: "
                        + " | ".join(details)
                    )

                return error_message

            # -----------------------------------------------------
            # MCP returned a successful response
            # -----------------------------------------------------
            if result.content:

                first = result.content[0]

                return getattr(
                    first,
                    "text",
                    str(first),
                )

            return (
                "Email tool completed without "
                "a text response."
            )