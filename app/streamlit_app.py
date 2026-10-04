from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.agent import MovieAgent
from core.config import settings
from core.ingest import ingest
from core.vector_store import MovieVectorStore


st.set_page_config(page_title="Movie Intelligence Assistant", page_icon="🎬", layout="wide")

st.title("🎬 Movie Intelligence & Follow-up Assistant")
st.caption("Subtitle RAG • Agentic routing • MCP email")

store = MovieVectorStore()

with st.sidebar:
    st.header("Knowledge Base")
    st.write(f"Indexed chunks: **{store.count()}**")
    titles = store.movie_titles()
    st.write(f"Movies: **{len(titles)}**")
    if titles:
        st.caption("Indexed movies")
        for title in titles:
            st.write(f"• {title}")
    if st.button("Rebuild subtitle index", use_container_width=True):
        try:
            with st.spinner("Parsing, embedding and indexing subtitles..."):
                ingest(reset=True)
            st.success("Index rebuilt.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

st.markdown("### Ask about a movie")
st.info(
    "Examples: `What happens when the captain discovers the power fault?`  "
    "or `Email a summary to you@example.com`."
)

query = st.chat_input("Ask a question or request an email...")

if query:
    with st.chat_message("user"):
        st.write(query)

    try:
        agent = MovieAgent()
        with st.chat_message("assistant"):
            with st.spinner("Thinking and retrieving subtitle evidence..."):
                result = agent.handle(query)

            if result["type"] == "clarification":
                st.warning(result["message"])
            elif result["type"] == "error":
                st.error(result["message"])
            elif result["type"] == "email":
                st.write(result["answer"])
                st.success(result["email_result"])
                with st.expander("Email content"):
                    st.text(result["email_body"])
            else:
                st.write(result["answer"])
                if result.get("sources"):
                    with st.expander("Retrieved subtitle sources"):
                        for source in result["sources"]:
                            st.markdown(
                                f"**{source['movie_title']} — {source['start']} → {source['end']}**\n\n"
                                f"> {source['dialogue']}"
                            )
    except Exception as exc:
        st.error(str(exc))
