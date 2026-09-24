# Local Document AI Agent (POC)

Terminal RAG agent: local LLM (Ollama) + real tool calling + ChromaDB for
vector search, plus a not-yet-wired-up FastAPI skeleton for what comes
next.

## Architecture at a glance

```
cli.py / api.py  (composition roots - pick concrete implementations)
      │
      ▼
    Agent  ──depends on──▶  ChatClient (interface)  ◀──implemented by──  OllamaChatClient
      │
      ▼
  tools.py  ──depends on──▶  EmbeddingClient (interface)  ◀──implemented by──  OllamaEmbeddingClient
      │
      ▼
  VectorStore  (wraps Chroma)
```

`Agent` never imports Ollama directly - it only knows about the
`ChatClient` interface (`llm/base.py`). `cli.py`/`api.py` are the only
places that decide "use Ollama" by constructing `OllamaChatClient()`. To
use a different model or provider later, write a new class implementing
`ChatClient` (or `EmbeddingClient`) and pass it in there - nothing in
`agent.py` or `tools.py` changes.

## 1. Start Ollama + ChromaDB

```
docker compose up -d
```

Then pull the two models Ollama needs (one for chat, one for embeddings):

```
docker exec -it ollama ollama pull llama3.1:8b
docker exec -it ollama ollama pull nomic-embed-text
```

## 2. Install the app

```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`.env` defaults assume Ollama/Chroma ports are published to the host
(true with the docker-compose.yml above) and this app runs on the host
too. If this app _also_ runs in a container on the same Docker network,
edit `.env` to use service names instead of `localhost` (comments in
`.env.example` explain exactly where).

The CLI and API emit timestamped operational logs. Set `LOG_LEVEL=DEBUG`
in `.env` to include Ollama request timings and detailed agent/tool flow;
logs include counts and durations but do not include document text or
prompts.

## 3. Run the terminal agent

```
cd src
python cli.py ../documents/sample.pdf
```

First run ingests the PDF into Chroma (extract → chunk → embed → store).
Later runs skip ingestion if the collection already has data.

```
You: How many vacation days do employees receive?
```

The agent decides when to call `search_document`, retrieves chunks from
Chroma, and only answers from what it retrieves - it's instructed to say
so if the document doesn't contain the answer, rather than guessing.

## 4. (Optional) Try the FastAPI skeleton

```
cd src
uvicorn api:app --reload
```

- `GET /health` — confirms it's up and which models it's configured for.
- `POST /chat` — `{"message": "..."}` → routes straight to the same
  `Agent` the CLI uses.
- `POST /documents` — stubbed, raises `NotImplementedError`. Wiring it up
  is just: accept an uploaded file, save it, call `ingest_pdf()` from
  `ingestion.py` (already used by `cli.py`) on it.

## 5. Project layout

```
local-document-agent/
├── documents/                    # put PDFs here
├── src/
│   ├── config.py                 # Settings - every env var, one place
│   ├── models.py                 # PageText / DocumentChunk / SearchResult
│   ├── document_loader.py        # PDF -> PageText[] (PyMuPDF)
│   ├── chunker.py                # PageText[] -> DocumentChunk[]
│   ├── llm/
│   │   ├── base.py               # ChatClient interface
│   │   └── ollama_client.py      # OllamaChatClient
│   ├── embeddings/
│   │   ├── base.py               # EmbeddingClient interface
│   │   └── ollama_embeddings.py  # OllamaEmbeddingClient
│   ├── vector_store.py           # Chroma HttpClient wrapper
│   ├── tools.py                  # search_document tool schema + impl
│   ├── agent.py                  # the tool-calling loop
│   ├── ingestion.py              # shared ingest logic (used by cli + api)
│   ├── cli.py                    # terminal entry point
│   └── api.py                    # FastAPI skeleton
├── requirements.txt
├── docker-compose.yml            # chromadb + ollama
└── .env.example
```

## 6. Known rough edges (expected for a POC)

- Chunking is a fixed character window, not sentence/paragraph aware.
  Good enough to validate the agent loop end to end; swap in something
  smarter once that's proven.
- `VectorStore`/`api.py` assume a single ingested document at a time.
- `max_tool_rounds` (default 4, in `.env`) is a safety cap against the
  model looping on tool calls without ever producing a final answer.
