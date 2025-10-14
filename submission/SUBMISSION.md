Blue Enigma — Submission Notes

This document summarizes what I built for the Blue Enigma Labs AI Engineer technical challenge and contains exact instructions for running and validating the project locally.

Repository contents (high level)
- src/neo4j_loader.py — loads `data/locations.csv` into Neo4j and can export a pyvis HTML visualization.
- src/pinecone_uploader.py — batches document embeddings from `data/docs.csv` and upserts into Pinecone with metadata and retries.
- src/embeddings.py — OpenAI embedding wrapper (call-time API key handling).
- src/hybrid_chat.py — hybrid retrieval pipeline that queries Pinecone and Neo4j, builds a combined prompt, and calls OpenAI to produce answers with citations.
- src/app.py — Streamlit demo with input box, citations, and embedded pyvis HTML visualization when available.
- tests/ — lightweight pytest tests (mocked where appropriate) to verify prompt building, module imports, and uploader logic.

What I implemented
- Safe import-time behavior: modules no longer initialize external services on import. This makes local testing and CI safer.
- Pinecone uploader with batching and retry/backoff, dry-run mode, and metadata preservation.
- Neo4j loader with MERGE semantics and an HTML visualization export using pyvis.
- Hybrid pipeline that fuses semantic and graph facts and returns LLM answers with citations.
- Streamlit demo that shows answers, supporting docs (Pinecone), and graph hits (Neo4j); it embeds `visualization/neo4j_graph.html` when present.
- Unit tests that avoid network calls by mocking external services.

How to run locally (PowerShell)
1. Create and activate a virtual environment:

   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt

2. Copy the env template and fill in keys (do not commit):

   Copy-Item .env.example .env
   # Edit .env and paste your OPENAI_API_KEY, PINECONE_API_KEY, NEO4J credentials

3. Start Neo4j (Docker recommended):

   docker run --name neo4j -p7474:7474 -p7687:7687 -e NEO4J_AUTH=neo4j/test neo4j:5

4. Load data & index documents:

   python src/neo4j_loader.py --csv data/locations.csv --visualize
   python src/pinecone_uploader.py --csv data/docs.csv

5. Run the demo:

   streamlit run src/app.py

6. Run tests:

   python -m pytest -q

Known limitations
- This submission assumes valid API keys for OpenAI and Pinecone and a running Neo4j instance for full end-to-end behavior.
- Tests include mocks for external services; full integration tests require credentials.

Contact
- If you need anything or want me to walk through parts of the code, you can reach me through the submission channel.
