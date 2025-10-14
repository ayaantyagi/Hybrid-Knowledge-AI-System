import os
import json
import time
import pandas as pd
from typing import List, Iterable
from tqdm import tqdm
from dotenv import load_dotenv
from src.embeddings import get_embeddings

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENVIRONMENT")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "blue-enigma-index")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 32))
RETRY_BACKOFF = float(os.getenv("RETRY_BACKOFF", 1.0))
RETRY_MAX = int(os.getenv("RETRY_MAX", 3))


def chunked(iterable: List, size: int) -> Iterable[List]:
    for i in range(0, len(iterable), size):
        yield iterable[i:i+size]


def _init_pinecone_if_needed(api_key: str = None, env: str = None):
    try:
        import pinecone
    except Exception as e:
        raise RuntimeError("pinecone package is required for Pinecone uploader") from e
    api_key = api_key or PINECONE_API_KEY
    env = env or PINECONE_ENV
    if not api_key:
        raise RuntimeError("PINECONE_API_KEY must be set to upload to Pinecone")
    pinecone.init(api_key=api_key, environment=env)
    return pinecone


def create_index_if_missing(pinecone, dim: int):
    if INDEX_NAME not in pinecone.list_indexes():
        pinecone.create_index(INDEX_NAME, dimension=dim, metric="cosine")
    return pinecone.Index(INDEX_NAME)


def upload_docs(csv_path: str = "data/docs.csv", dry_run: bool = False):
    """Read CSV, compute embeddings in batches, and upsert to Pinecone.

    CSV must contain columns: id, text, metadata (JSON string).
    """
    df = pd.read_csv(csv_path)
    texts = df["text"].astype(str).tolist()
    ids = df["id"].astype(str).tolist()
    # parse metadata safely
    metadata = []
    for m in df["metadata"].astype(str).tolist():
        try:
            metadata.append(json.loads(m))
        except Exception:
            metadata.append({"source": m})

    # compute embeddings in batches (streaming to avoid high memory use)
    all_embs = []
    print("🔢 Computing embeddings in batches...")
    for batch in chunked(texts, BATCH_SIZE):
        embs = get_embeddings(batch)
        all_embs.extend(embs)

    if not all_embs:
        print("No embeddings generated — nothing to upload.")
        return

    pinecone = _init_pinecone_if_needed()
    index = create_index_if_missing(pinecone, len(all_embs[0]))

    if dry_run:
        print(f"Dry run: would upsert {len(ids)} vectors to index {INDEX_NAME}")
        return

    print("📤 Uploading vectors to Pinecone...")
    # Upsert in batches with retry
    for id_batch, emb_batch, meta_batch in zip(chunked(ids, BATCH_SIZE), chunked(all_embs, BATCH_SIZE), chunked(metadata, BATCH_SIZE)):
        vectors = [(id_batch[j], emb_batch[j], meta_batch[j]) for j in range(len(id_batch))]
        for attempt in range(1, RETRY_MAX + 1):
            try:
                index.upsert(vectors=vectors)
                break
            except Exception as e:
                if attempt == RETRY_MAX:
                    raise
                wait = RETRY_BACKOFF * attempt
                print(f"Upsert failed (attempt {attempt}), retrying in {wait}s... Error: {e}")
                time.sleep(wait)

    print("✅ Pinecone upload complete!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Embed documents and upload to Pinecone")
    parser.add_argument("--csv", default="data/docs.csv", help="Path to docs CSV")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually upload; just compute embeddings")
    args = parser.parse_args()
    upload_docs(args.csv, dry_run=args.dry_run)
