# Codebase Q&A

A fullstack web app that answers natural language questions about a codebase using Retrieval-Augmented Generation (RAG). Paste a public GitHub repo URL, ingest it, and ask how a module works, where a feature is implemented, or what a function does — it retrieves the relevant code and generates a grounded answer with source references.

---

## How It Works

1. **Ingestion** — Submit a repo URL in the web UI (or `POST /api/ingest`). The backend clones the repo, chunks the source files into overlapping 50-line windows, embeds each chunk using Voyage AI (`voyage-code-3`), and stores the vectors in PostgreSQL with pgvector. Ingestion runs as a background job; the UI polls for status.
2. **Retrieval** — When a question comes in, it's embedded with the same model and a cosine similarity search returns the most relevant code chunks.
3. **Agentic Generation** — Claude is given a `search_codebase` tool it can invoke multiple times with different queries to gather enough context before answering. It decides what to search and when — not the application.
4. **Web Interface** — A React frontend lets you ingest a repo and chat with it, showing the answer alongside the source files it was grounded in.

```
Ask: How does authentication work?
  → Claude calls search_codebase("auth middleware") → pgvector search
  → Claude calls search_codebase("session token") → pgvector search
  → Claude answers with sources → rendered in chat
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript + Vite |
| Backend | Python 3.11+, FastAPI |
| Vector Database | PostgreSQL + pgvector |
| Embeddings | Voyage AI `voyage-code-3` |
| LLM | Claude (`claude-haiku-4-5`) |
| Deployment | Docker (single image serving API + static frontend) |

---

## Project Structure

```
slack-codebase-agent/
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx        # Chat UI + repo ingest form
│   │   ├── api.ts         # Fetch client for the backend API
│   │   └── ...
│   └── vite.config.ts     # Dev server proxies /api → localhost:8000
│
├── ingestion/
│   ├── clone.py          # Clone target repo to temp directory
│   ├── chunker.py        # Walk files, split into overlapping chunks
│   ├── embedder.py       # Embed chunks via Voyage AI
│   ├── store.py          # Insert vectors + metadata into pgvector
│   └── pipeline.py       # Wire clone → chunk → embed → store
│
├── retrieval/
│   └── search.py         # Cosine similarity query against pgvector
│
├── agent/
│   └── agent.py          # ask(): retrieve chunks, call Claude, return answer
│
├── api/
│   ├── main.py           # FastAPI app entry point, serves the built frontend
│   └── routes.py         # POST /api/query, POST /api/ingest, GET /api/ingest/{job_id}
│
├── db/
│   └── schema.sql        # Table definition for chunks and vectors
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL with the `pgvector` extension enabled (or Docker)
- A Voyage AI API key
- An Anthropic API key

### 1. Clone the repo

```bash
git clone https://github.com/your-username/slack-codebase-agent.git
cd slack-codebase-agent
```

### 2. Install backend dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Fill in `.env`:

```
VOYAGE_API_KEY=
ANTHROPIC_API_KEY=
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

### 5. Set up the database

```bash
psql $DATABASE_URL -f db/schema.sql
```

Or with Docker:

```bash
docker run -d --name pgvector -e POSTGRES_PASSWORD=postgres -p 5432:5432 pgvector/pgvector:pg17
docker exec -i pgvector psql -U postgres -d postgres < db/schema.sql
```

### 6. Run it

In one terminal, start the API:

```bash
uvicorn api.main:app --reload --port 8000
```

In another, start the frontend dev server (proxies `/api` to the backend):

```bash
cd frontend
npm run dev
```

Open the printed local URL (default `http://localhost:5173`).

---

## Usage

1. Paste a public GitHub repo URL into the "Ingest repo" field and submit. Ingestion runs in the background; the status bar updates when it's done.
2. Ask questions in the chat box, e.g.:
   - How does authentication work?
   - Where is rate limiting implemented?
   - What does this project do?
3. Answers appear in the chat with pills for each source file they were grounded in.

---

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/query` | `{ "question": string }` → `{ "answer": string, "sources": [...] }` |
| `POST` | `/api/ingest` | `{ "repo_url": string }` → `{ "job_id": string }`, starts a background ingest job |
| `GET` | `/api/ingest/{job_id}` | `{ "status": "running" \| "done" \| "error", "repo_url": string, "error": string \| null }` |

---

## Deployment

The `Dockerfile` builds the frontend and bundles the static assets into the FastAPI image, so a single container serves both the UI and the API:

```bash
docker build -t codebase-qa .
docker run -p 8000:8000 --env-file .env codebase-qa
```

Point `DATABASE_URL` at a managed PostgreSQL instance with pgvector enabled (e.g. a Render Postgres add-on).

---

## Key Concepts

**Chunking** — Source files are split into overlapping 50-line windows with a 10-line overlap to preserve context at boundaries.

**RAG** — Retrieval-Augmented Generation grounds Claude's response in actual retrieved code rather than relying on parametric memory, reducing hallucination and keeping answers traceable to source.

**Agentic retrieval** — Claude is given a `search_codebase` tool and controls the retrieval strategy itself. It can issue multiple queries (e.g. "JWT middleware", then "session token verification") before answering — multi-hop reasoning that single-shot RAG can't do.

**pgvector** — A PostgreSQL extension that stores and queries high-dimensional vectors natively, enabling cosine similarity search without a separate vector database service.

---

## License

MIT
