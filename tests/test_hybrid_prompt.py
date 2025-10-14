from src.hybrid_chat import build_prompt


def test_build_prompt_basic():
    docs = [{"id": "doc1", "metadata": {"text_snippet": "foo snippet", "source": "wiki"}}]
    graph = [{"id": "g1", "name": "Place", "description": "A nice place"}]
    prompt = build_prompt("Tell me about Place", docs, graph)
    assert "Documents:" in prompt
    assert "Graph facts:" in prompt
    assert "Tell me about Place" in prompt
    assert "foo snippet" in prompt
