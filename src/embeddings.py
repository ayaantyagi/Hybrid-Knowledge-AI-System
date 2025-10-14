import os
import openai
from dotenv import load_dotenv

load_dotenv()

def get_embeddings(texts, model="text-embedding-3-small"):
    """Return embeddings for a list of texts.

    This function sets the OpenAI API key at call time (not import time)
    so importing this module won't fail during tests when the env var
    isn't present.
    """
    if isinstance(texts, str):
        texts = [texts]
    openai.api_key = os.getenv("OPENAI_API_KEY")
    # OpenAI Python client new style: openai.Embedding.create
    resp = openai.Embedding.create(model=model, input=texts)
    return [r['embedding'] for r in resp['data']]
