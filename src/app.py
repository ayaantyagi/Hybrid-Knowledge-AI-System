import os
import streamlit as st
from src.hybrid_chat import answer_query, pinecone_search, neo4j_search
import time

st.set_page_config(page_title="Blue Enigma Hybrid Chat", page_icon="🧠")
st.title("🧠 Blue Enigma — Hybrid AI Chat")

st.sidebar.header("Settings")
top_k = st.sidebar.slider("Pinecone top_k", min_value=1, max_value=10, value=3)
show_visual = st.sidebar.checkbox("Show graph visualization (if generated)", value=True)
prewarm = st.sidebar.checkbox("Pre-warm Pinecone & Neo4j clients (reduces first-query latency)", value=False)
clear_cache = st.sidebar.button("Clear in-memory caches")

query = st.text_input("Ask your question about any location:")
if prewarm:
    # attempt to initialize external clients once to reduce latency on first query
    try:
        from src.hybrid_chat import _get_pinecone_index, _get_neo4j_driver
        _get_pinecone_index()
        _get_neo4j_driver()
        st.sidebar.info("Clients pre-warmed")
    except Exception as e:
        st.sidebar.error(f"Pre-warm failed: {e}")

if clear_cache:
    try:
        pinecone_search.cache_clear()
        neo4j_search.cache_clear()
        st.sidebar.success("Caches cleared")
    except Exception as e:
        st.sidebar.error(f"Failed to clear caches: {e}")
if st.button("Ask") and query:
    with st.spinner("Thinking..."):
        try:
            # measure latency
            start = time.perf_counter()
            answer = answer_query(query)
            elapsed = time.perf_counter() - start
        except Exception as e:
            st.error(f"Error while answering: {e}")
            answer = None
            elapsed = None

    if answer:
        st.markdown("### 🤖 Answer:")
        st.write(answer)
        if elapsed is not None:
            st.info(f"Query latency: {elapsed:.2f} seconds")

        # Show supporting documents from Pinecone (best-effort)
        try:
            docs = pinecone_search(query, top_k=top_k)
            if docs:
                st.markdown("#### 📄 Supporting documents (Pinecone):")
                for d in docs:
                    meta = d.get('metadata', {})
                    st.write(f"- {meta.get('text_snippet', meta.get('source',''))} (id: {d.get('id')}, score: {d.get('score')})")
        except Exception:
            # ignore failures to query Pinecone; user may not have API keys locally
            pass

        # Show Neo4j graph search results (best-effort)
        try:
            graph_hits = neo4j_search(query)
            if graph_hits:
                st.markdown("#### 🗺️ Graph hits (Neo4j):")
                for g in graph_hits:
                    st.write(f"- {g.get('name')} — {g.get('description')} (id: {g.get('id')})")
        except Exception:
            pass

    # optionally embed the pyvis HTML visualization
    if show_visual:
        viz_path = os.path.join("visualization", "neo4j_graph.html")
        if os.path.exists(viz_path):
            st.markdown("#### 🌐 Graph visualization")
            with open(viz_path, 'r', encoding='utf-8') as f:
                html = f.read()
            st.components.v1.html(html, height=700)
