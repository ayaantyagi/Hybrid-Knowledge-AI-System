# Blue Enigma — Hybrid Knowledge AI System

[![CI](https://github.com/ayaantyagi/BLUE-ENIGMA-AL/actions/workflows/ci.yml/badge.svg)](https://github.com/ayaantyagi/BLUE-ENIGMA-AL/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Summary
This project implements a hybrid retrieval + reasoning pipeline using:
- **Neo4j** for structured, graph knowledge (locations & relations),
- **Pinecone** for semantic retrieval over documents,
- **OpenAI GPT** for reasoning and natural language responses.

## Quick start (Windows / PowerShell) 

1. Clone the repo and change into it: 

   git clone <repo-url>
   cd blue-enigma-ai

2. Copy the example env and fill in secrets:

   Copy-Item .env.example .env
   # then open .env and paste keys for OpenAI, Pinecone, Neo4j

3. Bootstrap the Python environment (PowerShell):

   .\setup.ps1

   To also run tests during setup:

   .\setup.ps1 -RunTests

4. Start Neo4j (Desktop or Docker). Example Docker:

   docker run --name neo4j -p7474:7474 -p7687:7687 -e NEO4J_AUTH=neo4j/test neo4j:5

5. Load data (after setting .env and starting Neo4j):

   python src/neo4j_loader.py
   python src/pinecone_uploader.py

6. Run the Streamlit demo:

   streamlit run src/app.py

## Files
- `src/neo4j_loader.py` — loads location csv into Neo4j
- `src/pinecone_uploader.py` — embeds & upserts docs to Pinecone
- `src/embeddings.py` — OpenAI embedding helper
- `src/hybrid_chat.py` — main pipeline that fuses Pinecone + Neo4j
- `src/app.py` — simple Streamlit demo

# Blue Enigma — Hybrid Knowledge AI System

Brief: this project implements a hybrid retrieval + reasoning pipeline that combines a vector DB (Pinecone), a graph DB (Neo4j), and OpenAI GPT models to answer location-based questions with citations from both documents and graph facts.

This README is tailored for the Blue Enigma Labs technical challenge submission and includes setup, architecture, component contracts, run/test instructions, and a short 2-minute Loom script you can record.

## Architecture (high level)

- Ingest: `data/docs.csv` -> `src/pinecone_uploader.py` -> Pinecone (embedding + upsert)
- Graph: `data/locations.csv` -> `src/neo4j_loader.py` -> Neo4j; optional HTML export via `pyvis`
- Retrieval & Reasoning: `src/hybrid_chat.py` combines Pinecone (semantic docs) + Neo4j (structured facts) to build a prompt and call OpenAI to produce an answer with citations
- UI: `src/app.py` (Streamlit) exposes an interactive demo showing answer, supporting docs, and graph hits/visualization

## Component contracts (brief)

- `src.embeddings.get_embeddings(texts: str|List[str], model: str) -> List[List[float]]`
  - Inputs: a string or list of strings
  - Output: list of embedding vectors (list of floats)
  - Error: raises RuntimeError if `OPENAI_API_KEY` is missing

- `src.pinecone_uploader.upload_docs(csv_path: str, dry_run: bool)`
  - Inputs: path to `docs.csv` containing `id,text,metadata` (metadata is JSON string)
  - Behavior: batches texts, calls `get_embeddings`, upserts (idempotent) into index
  - Errors: raises RuntimeError if `PINECONE_API_KEY` missing or pinecone lib not installed

- `src.neo4j_loader.load_locations(csv_path: str)`
  - Inputs: path to `locations.csv` with columns `id,name,lat,lon,description,tags`
  - Behavior: MERGE nodes with uniqueness constraint on `id` and optional visualization export
  - Errors: raises RuntimeError if Neo4j env vars missing or `neo4j` lib not installed

- `src.hybrid_chat.answer_query(query: str) -> str`
  - Inputs: natural language query
  - Behavior: queries Pinecone and Neo4j, builds a combined prompt, calls OpenAI ChatCompletion, returns generated text
  - Errors: clear runtime errors when OpenAI or required env vars are missing

## Data format

- `data/docs.csv` (example rows provided in repo): columns `id,text,metadata` where `metadata` is a JSON string containing keys like `source`, `text_snippet`, `neo4j_id`.
- `data/locations.csv` (expected): `id,name,lat,lon,description,tags` (CSV headers must match)

## Required environment variables (.env)

Copy `.env.example` -> `.env` and fill values.

- OPENAI_API_KEY — API key for OpenAI
- OPENAI_MODEL — Chat model for reasoning (e.g., `gpt-4o-mini` or `gpt-4o`) or embedding model for embeddings
- PINECONE_API_KEY, PINECONE_ENVIRONMENT, PINECONE_INDEX_NAME
- NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

## Setup (Windows / PowerShell)

1. Create and activate a venv (or run the provided helper):

```powershell
# create venv (only once)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# install dependencies
pip install -r requirements.txt

# optional helper that automates the above
.\setup.ps1
```

2. Fill `.env` with the keys above.

3. Start Neo4j (recommended: Docker):

```powershell
docker run --name neo4j -p7474:7474 -p7687:7687 -e NEO4J_AUTH=neo4j/test neo4j:5
```

4. Load data:

```powershell
python src/neo4j_loader.py --csv data/locations.csv --visualize
python src/pinecone_uploader.py --csv data/docs.csv
```

5. Run the demo:

```powershell
streamlit run src/app.py
```

## Running tests

The repository includes lightweight unit tests that avoid calling external services directly. Run:

```powershell
python -m pytest -q
```

If you get import/runtime errors about missing packages, activate the venv and install `requirements.txt` first.

## Submission checklist

- [ ] Repository with working code (this repo)
- [ ] Filled `.env` (do not commit; provide instructions to reviewer)
- [ ] Short `README.md` (this file)
- [ ] Optional: short Loom video (script below)

When you submit, include a short note describing what works locally and any known limitations (e.g., missing API keys, if you used fake data, etc.).

---

## Continuous integration & publishing

This repo includes a basic GitHub Actions workflow that runs the tests on push: `.github/workflows/ci.yml`.

To publish to GitHub from PowerShell, use the included helper script `publish.ps1`:

```powershell
# create and push repository (requires gh CLI for automatic creation)
.\publish.ps1 -RepoName blue-enigma-ai -Visibility private
```

The repository also includes an `LICENSE` (MIT) file. Update it if you want a different license.

