import importlib


def test_embeddings_module_importable():
    mod = importlib.import_module('src.embeddings')
    assert hasattr(mod, 'get_embeddings')
    func = getattr(mod, 'get_embeddings')
    assert callable(func)
