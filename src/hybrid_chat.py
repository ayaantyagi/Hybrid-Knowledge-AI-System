import os
from dotenv import load_dotenv
from src.embeddings import get_embeddings
import openai
import json

load_dotenv()

# Don't initialize external clients at import time. Create them when needed so
# importing this module is safe during tests or in environments without
# configured services.

def _get_pinecone_index():
    try:
        import pinecone
    except Exception as e:
        raise RuntimeError("pinecone package is required for pinecone_search") from e
    api_key = os.getenv("PINECONE_API_KEY")
    env = os.getenv("PINECONE_ENVIRONMENT")
    index_name = os.getenv("PINECONE_INDEX_NAME")
    if not api_key or not index_name:
        raise RuntimeError("PINECONE_API_KEY and PINECONE_INDEX_NAME must be set for pinecone_search")
    pinecone.init(api_key=api_key, environment=env)
    return pinecone.Index(index_name)

def pinecone_search(query, top_k=3):
    index = _get_pinecone_index()
    q_emb = get_embeddings(query)[0]
    res = index.query(vector=q_emb, top_k=top_k, include_metadata=True)
    # format results
    hits = []
    for m in res.get('matches', []):
        hits.append({
            "id": m['id'],
            "score": m.get('score'),
            "metadata": m.get('metadata', {})
        })
    return hits

def neo4j_search(query, limit=3):
    try:
        from neo4j import GraphDatabase
    except Exception as e:
        raise RuntimeError("neo4j package is required for neo4j_search") from e
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    if not uri or not user or not password:
        raise RuntimeError("NEO4J_URI/NEO4J_USER/NEO4J_PASSWORD must be set for neo4j_search")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    cypher = '''
    MATCH (l:Location)
    WHERE toLower(l.name) CONTAINS toLower($query) OR toLower(l.description) CONTAINS toLower($query)
    RETURN l.id AS id, l.name AS name, l.description AS description
    LIMIT $limit
    '''
    with driver.session() as session:
        result = session.run(cypher, {"query": query, "limit": limit})
        data = [r.data() for r in result]
    driver.close()
    return data

def build_prompt(query, docs, graph):
    context_docs = "\n".join([f"[doc:{d['id']}] {d['metadata'].get('text_snippet', d['metadata'].get('source',''))}" for d in docs])
    context_graph = "\n".join([f"[graph:{g['id']}] {g.get('name','')} - {g.get('description','')}" for g in graph])
    return f"""You are an assistant that answers location/travel questions. Use the provided documents and graph facts to answer and include citations.

Documents:\n{context_docs}\n\nGraph facts:\n{context_graph}\n\nQuestion: {query}\n"""

def answer_query(query):
    # ensure OpenAI key is set at call-time
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        raise RuntimeError("OPENAI_API_KEY must be set to call answer_query")
    docs = pinecone_search(query)
    graph = neo4j_search(query)
    prompt = build_prompt(query, docs, graph)
    response = openai.ChatCompletion.create(
        model=os.getenv("OPENAI_MODEL"),
        messages=[
            {"role":"system","content":"You are a helpful AI assistant."},
            {"role":"user","content":prompt}
        ],
        temperature=0.2,
        max_tokens=400
    )
    return response['choices'][0]['message']['content']

if __name__ == "__main__":
    print(answer_query("Tell me about Central Park"))
