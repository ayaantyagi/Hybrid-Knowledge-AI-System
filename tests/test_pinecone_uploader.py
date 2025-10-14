import builtins
import json
import os
import pandas as pd
import importlib


def test_upload_docs_dry_run(tmp_path, monkeypatch):
    # prepare a small csv
    df = pd.DataFrame({
        'id': ['d1', 'd2'],
        'text': ['hello world', 'another doc'],
        'metadata': [json.dumps({'source': 'test'}), json.dumps({'source': 'test2'})]
    })
    csv_path = tmp_path / 'docs.csv'
    df.to_csv(csv_path, index=False)

    # mock get_embeddings to return fixed vectors
    mod = importlib.import_module('src.pinecone_uploader')
    monkeypatch.setattr('src.pinecone_uploader.get_embeddings', lambda texts: [[0.1, 0.2]] * len(texts))

    # mock pinecone init/list/create/Index/upsert
    class FakeIndex:
        def __init__(self, name):
            self.name = name

        def upsert(self, vectors=None):
            # basic validation
            assert vectors is not None

    class FakePinecone:
        def __init__(self):
            self._indexes = []

        def list_indexes(self):
            return self._indexes

        def create_index(self, name, dimension=None, metric=None):
            self._indexes.append(name)

        def Index(self, name):
            return FakeIndex(name)

    fake_pc = FakePinecone()

    monkeypatch.setattr('src.pinecone_uploader._init_pinecone_if_needed', lambda: fake_pc)

    # call upload_docs in dry-run and real mode to verify behavior
    # dry-run should not call upsert
    mod.upload_docs(str(csv_path), dry_run=True)

    # now run without dry-run to exercise upsert (monkeypatched Index.upsert asserts)
    mod.upload_docs(str(csv_path), dry_run=False)
