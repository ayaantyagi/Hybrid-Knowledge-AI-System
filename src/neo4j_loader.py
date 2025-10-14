import pandas as pd
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


class Neo4jClient:
    """Light wrapper around neo4j driver that defers imports until used."""
    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        try:
            from neo4j import GraphDatabase
        except Exception as e:
            raise RuntimeError("neo4j package is required to use Neo4jClient") from e
        uri = uri or NEO4J_URI
        user = user or NEO4J_USER
        password = password or NEO4J_PASSWORD
        if not uri or not user or not password:
            raise RuntimeError("NEO4J_URI/NEO4J_USER/NEO4J_PASSWORD must be set to connect to Neo4j")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def run(self, query: str, params: Optional[dict] = None):
        with self.driver.session() as session:
            return list(session.run(query, params or {}))


def load_locations(csv_path: str = "data/locations.csv"):
    """Load locations from CSV into Neo4j.

    The CSV should have at least columns: id, name, lat, lon. Optional: description, tags.
    """
    df = pd.read_csv(csv_path)
    client = Neo4jClient()

    # Create uniqueness constraint (syntax varies by Neo4j version)
    try:
        client.run("CREATE CONSTRAINT IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE")
    except Exception:
        # older servers may use different syntax
        try:
            client.run("CREATE CONSTRAINT IF NOT EXISTS ON (l:Location) ASSERT l.id IS UNIQUE")
        except Exception:
            # Not critical; continue
            pass

    # Use a single session for performance
    for _, row in df.iterrows():
        params = {
            "id": str(row.get('id', '')),
            "name": row.get('name', ''),
            "lat": float(row.get('lat') or 0.0),
            "lon": float(row.get('lon') or 0.0),
            "description": row.get('description', '') if 'description' in row else '',
            "tags": row.get('tags', '') if 'tags' in row else ''
        }
        client.run(
            """
            MERGE (l:Location {id: $id})
            SET l.name = $name, l.lat = $lat, l.lon = $lon, l.description = $description, l.tags = $tags
            """,
            params,
        )

    client.close()
    print("✅ Loaded locations into Neo4j successfully!")


def visualize_graph(output_html: str = "visualization/neo4j_graph.html", limit: int = 500):
    """Export a simple interactive HTML visualization of the Location subgraph using pyvis.

    This will query nodes labeled `Location` and relationships between them (if any) and
    produce an HTML file that can be opened in the browser.
    """
    try:
        from pyvis.network import Network
    except Exception as e:
        raise RuntimeError("pyvis is required for visualization. Install via pip: pip install pyvis") from e

    client = Neo4jClient()
    # fetch nodes
    nodes_q = "MATCH (l:Location) RETURN l.id AS id, l.name AS name, l.description AS description LIMIT $limit"
    rels_q = "MATCH (a:Location)-[r]->(b:Location) RETURN a.id AS a, b.id AS b, type(r) AS type LIMIT $limit"
    nodes = client.run(nodes_q, {"limit": limit})
    rels = client.run(rels_q, {"limit": limit})

    net = Network(height="800px", width="100%", bgcolor="#ffffff", font_color="#222222")
    id_to_label = {}
    for record in nodes:
        nid = record['id']
        label = record.get('name') or str(nid)
        title = record.get('description') or ''
        net.add_node(nid, label=label, title=title)
        id_to_label[nid] = label

    for record in rels:
        a = record['a']
        b = record['b']
        rtype = record.get('type') or ''
        if a in id_to_label and b in id_to_label:
            net.add_edge(a, b, title=rtype)

    # ensure output dir exists
    out_dir = os.path.dirname(output_html)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    net.show(output_html)
    client.close()
    print(f"✅ Graph visualization written to {output_html}")


if __name__ == "__main__":
    # simple CLI behavior
    import argparse

    parser = argparse.ArgumentParser(description="Load locations into Neo4j and optionally visualize")
    parser.add_argument("--csv", default="data/locations.csv", help="Path to locations CSV")
    parser.add_argument("--visualize", action="store_true", help="Export an interactive HTML visualization")
    parser.add_argument("--out", default="visualization/neo4j_graph.html", help="Visualization output HTML")
    args = parser.parse_args()

    load_locations(args.csv)
    if args.visualize:
        visualize_graph(args.out)
