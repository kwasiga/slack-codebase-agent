# Slack Codebase Q&A Agent

A Slack bot that answers natural language questions about a codebase using Retrieval-Augmented Generation (RAG). Ask it how a module works, where a feature is implemented, or what a function does — it retrieves the relevant code and generates a grounded answer.

---

## How It Works

1. **Ingestion** — A one-time pipeline clones a GitHub repo, chunks the source files, embeds each chunk using Voyage AI (`voyage-code-3`), and stores the vectors in a PostgreSQL database with pgvector.
2. **Retrieval** — When a query comes in, it's embedded with the same model, and a cosine similarity search returns the most relevant code chunks.
3. **Generation** — Claude receives the query and retrieved chunks, uses a `search_codebase` tool to re-query if needed, and returns a grounded answer.
4. **Slack Interface** — A Slack Bolt app receives slash commands, calls the agent pipeline, and posts the response back to the channel with source file references.

```
/ask How does authentication work?
  → embed query → pgvector search → GPT-4o (with tool use) → Slack response
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Web Framework | FastAPI |
| Vector Database | PostgreSQL + pgvector |
| Embeddings | Voyage AI `voyage-code-3` |
| LLM | Claude with tool use |
| Slack | Slack Bolt SDK |
| Deployment | Render |

---

## Project Structure

```
slack-codebase-agent/
│
├── ingestion/
│   ├── clone.py          # Clone target repo to temp directory
│   ├── chunker.py        # Walk files, split into overlapping chunks
│   ├── embedder.py       # Embed chunks via Voyage AI
│   ├── store.py          # Insert vectors + metadata into pgvector
│   └── pipeline.py       # Wire clone → chunk → embed → store
│
├── retrieval/
│   ├── search.py         # Cosine similarity query against pgvector
│   └── rerank.py         # Optional reranking of top-k results
│
├── agent/
│   ├── tools.py          # search_codebase tool definition for GPT-4o
│   ├── prompt.py         # System prompt and context assembly
│   └── run.py            # Agentic loop: LLM call, tool use, final answer
│
├── api/
│   ├── main.py           # FastAPI app entry point
│   └── routes.py         # POST /query, POST /slack/events
│
├── slack/
│   ├── bot.py            # Slack Bolt app setup
│   └── handlers.py       # Slash command and event handlers
│
├── db/
│   ├── client.py         # psycopg2 connection pool
│   └── schema.sql        # Table definition for chunks and vectors
│
├── config.py             # Environment variable loading
├── requirements.txt
├── .env.example
├── Dockerfile
└── README.md
```

---

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL with the `pgvector` extension enabled
- A Voyage AI API key
- An Anthropic API key
- A Slack app with slash command and bot token scopes

### 1. Clone the repo

```bash
git clone https://github.com/your-username/slack-codebase-agent.git
cd slack-codebase-agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Fill in `.env`:

```
VOYAGE_API_KEY=
ANTHROPIC_API_KEY=
DATABASE_URL=postgresql://user:password@host:5432/dbname
SLACK_BOT_TOKEN=
SLACK_SIGNING_SECRET=
TARGET_REPO_URL=https://github.com/target/repo
```

### 4. Set up the database

```bash
psql $DATABASE_URL -f db/schema.sql
```

### 5. Run ingestion

```bash
python -m ingestion.pipeline
```

### 6. Start the API server

```bash
uvicorn api.main:app --reload
```

### 7. Connect Slack

Expose your local server with [ngrok](https://ngrok.com/) during development:

```bash
ngrok http 8000
```

Set the slash command request URL in your Slack app dashboard to:
```
https://your-ngrok-url.ngrok.io/slack/events
```

---

## Usage

In any Slack channel where the bot is present:

```
/ask How does the authentication middleware work?
/ask Where is rate limiting implemented?
/ask What does the chunker module do?
```

The bot will respond with a generated answer and the source files it referenced.

---

## Deployment

The app is configured for deployment on [Render](https://render.com).

- The FastAPI app runs as a web service
- PostgreSQL with pgvector is provisioned as a managed database
- Environment variables are set via the Render dashboard
- The ingestion pipeline can be triggered as a one-off job

---

## Key Concepts

**Chunking** — Source files are split into overlapping windows (e.g. 50 lines with 10-line overlap) to preserve context at boundaries. Chunks are kept under ~512 tokens to maximize embedding precision.

**RAG** — Retrieval-Augmented Generation grounds the LLM's response in actual retrieved code rather than relying on parametric memory, reducing hallucination and keeping answers traceable to source.

**Agentic retrieval** — Claude is given a `search_codebase` tool it can invoke mid-generation if the initial retrieval isn't sufficient. This allows multi-hop reasoning across the codebase.

**pgvector** — A PostgreSQL extension that stores and queries high-dimensional vectors natively, enabling cosine similarity search without a separate vector database service.

---

## License

MIT