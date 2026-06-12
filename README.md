# Slack Codebase Q&A Agent

A Slack bot that answers natural language questions about a codebase using Retrieval-Augmented Generation (RAG). Ask it how a module works, where a feature is implemented, or what a function does — it retrieves the relevant code and generates a grounded answer.

---

## How It Works

1. **Ingestion** — Run `/ingest <github-url>` to clone a repo, chunk the source files, embed each chunk using Voyage AI (`voyage-code-3`), and store the vectors in PostgreSQL with pgvector.
2. **Retrieval** — When a query comes in, it's embedded with the same model and a cosine similarity search returns the most relevant code chunks.
3. **Generation** — Claude receives the query and retrieved chunks and returns a grounded answer.
4. **Slack Interface** — A Slack Bolt app receives slash commands via socket mode and posts the response back to the channel.

```
/ask How does authentication work?
  → embed query → pgvector search → Claude → Slack response
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Web Framework | FastAPI |
| Vector Database | PostgreSQL + pgvector |
| Embeddings | Voyage AI `voyage-code-3` |
| LLM | Claude (`claude-opus-4-8`) |
| Slack | Slack Bolt SDK (socket mode) |
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
│   └── search.py         # Cosine similarity query against pgvector
│
├── agent/
│   └── agent.py          # ask(): retrieve chunks, call Claude, return answer
│
├── api/
│   ├── main.py           # FastAPI app entry point
│   └── routes.py         # POST /query
│
├── slack/
│   └── bot.py            # Slack Bolt app, /ask and /ingest handlers
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
- PostgreSQL with the `pgvector` extension enabled (or Docker)
- A Voyage AI API key
- An Anthropic API key
- A Slack app with `/ask` and `/ingest` slash commands, socket mode enabled

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
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=
SLACK_APP_TOKEN=xapp-...
```

### 4. Set up the database

```bash
psql $DATABASE_URL -f db/schema.sql
```

Or with Docker:

```bash
docker run -d --name pgvector -e POSTGRES_PASSWORD=postgres -p 5432:5432 pgvector/pgvector:pg17
docker exec -i pgvector psql -U postgres -d postgres < db/schema.sql
```

### 5. Start the bot

```bash
python -m slack.bot
```

---

## Usage

In any Slack channel where the bot is present:

```
/ingest https://github.com/some/repo
/ask How does authentication work?
/ask Where is rate limiting implemented?
/ask What does this project do?
```

The bot will ingest any public GitHub repo on demand and answer questions grounded in the actual source code.

---

## Deployment

The app is configured for deployment on [Render](https://render.com).

- Run `python -m slack.bot` as the start command
- PostgreSQL with pgvector is provisioned as a managed database
- Environment variables are set via the Render dashboard

---

## Key Concepts

**Chunking** — Source files are split into overlapping 50-line windows with a 10-line overlap to preserve context at boundaries.

**RAG** — Retrieval-Augmented Generation grounds Claude's response in actual retrieved code rather than relying on parametric memory, reducing hallucination and keeping answers traceable to source.

**pgvector** — A PostgreSQL extension that stores and queries high-dimensional vectors natively, enabling cosine similarity search without a separate vector database service.

---

## License

MIT
