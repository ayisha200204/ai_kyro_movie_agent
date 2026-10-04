# Movie Intelligence & Follow-up Assistant

AI KYRO internship technical task implementation.

## What it does

- Parses `.srt` subtitles for up to 100 movies.
- Cleans subtitle text and creates overlapping dialogue-context chunks.
- Preserves movie title, start/end timestamps, cue ranges, and dialogue.
- Creates vector embeddings and stores them in ChromaDB.
- Uses RAG to answer movie questions with precise `Movie — timestamp` citations.
- Routes informational queries to RAG.
- Routes email/action requests through the RAG layer and an MCP email tool.
- Asks for clarification when movie title or recipient information is missing/ambiguous.
- Provides a simple Streamlit interface.

## Architecture

```text
SRT files -> Parser -> Context chunks -> Gemini embeddings -> ChromaDB
                                                    |
User -> Intent Router -> RAG Retriever -------------+-> Gemini answer -> citations
             |
             +-> Action request -> RAG -> MCP email tool -> SMTP
             |
             +-> Ambiguous -> clarification
```

## Requirements

Python 3.10+ and an internet connection for Gemini API calls.

The project uses the official MCP Python SDK. The current v2 SDK uses `MCPServer`, and its stdio client transport can launch a local MCP server as a subprocess.

## Setup

### 1. Create environment

```bash
python -m venv .venv
# Windows PowerShell
.venv\\Scripts\\Activate.ps1
# macOS/Linux
source .venv/bin/activate
```

### 2. Install

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Copy `.env.example` to `.env` and set `GEMINI_API_KEY`.

For real email dispatch, configure SMTP credentials. For Gmail, use an App Password rather than your normal account password.

### 4. Add subtitle files

Put `.srt` files into:

```text
data/subtitles/
```

The filename becomes the movie title. For example:

```text
The Matrix.srt
Inception.srt
```

The ingestion pipeline accepts up to 100 `.srt` files.

### 5. Build the index

```bash
python -m core.ingest
```

To rebuild from scratch:

```bash
python -m core.ingest --reset
```

### 6. Run the app

```bash
streamlit run app/streamlit_app.py
```

## Example queries

Informational:

- `What happens when Neo first meets Morpheus?`
- `What does the character say about the Matrix?`
- `Find the scene where two characters discuss the plan.`

Action:

- `Email me a summary of the scene where Neo meets Morpheus.`
- `Send a quote analysis from The Matrix to alice@example.com.`

Ambiguous:

- `What happens in the movie?` -> asks which movie.
- `Email me the scene.` -> asks which scene/movie and recipient.

## Email safety

The MCP email tool only sends when the user provides a syntactically valid recipient. If SMTP is not configured, the tool returns a clear configuration error instead of pretending an email was sent.

## Testing

```bash
pytest -q
```

## Submission notes

Do not commit `.env`, API keys, passwords, or private subtitle datasets. Commit the source code and a small synthetic/demo dataset only if needed.
