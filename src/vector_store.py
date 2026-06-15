"""
Milestone 4 — Embed chunks, store in ChromaDB, and test retrieval.

Pipeline (see planning.md architecture diagram):
    chunks.json  ->  bge-m3 embeddings  ->  ChromaDB (cosine)  ->  top-k retrieval

Embedding model: all-MiniLM-L6-v2 (sentence-transformers). 384-dim, runs locally with no API
key or rate limits, ~80MB. (planning.md originally specified bge-m3; switched to MiniLM for the
lightweight local default — see the Retrieval Approach note in planning.md.) Embeddings are
L2-normalized and the collection uses cosine space, so distances fall in [0, 2] where 0 =
identical — that makes the "distance < 0.5" checkpoint meaningful.

Run directly to (re)build the index and run the evaluation queries:
    python src/vector_store.py
Import `retrieve` from this module in Milestone 5.
"""

import json
import os

import chromadb

CHUNKS_PATH = "data/chunks.json"
DB_PATH = "chroma_db"
COLLECTION = "unofficial_guide"
MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 5

_model = None
_collection = None


def get_model():
    """Load bge-m3 once and reuse it."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        print(f"[model] loading {MODEL_NAME} (first run downloads ~80MB)...")
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed(texts):
    """Encode a list of texts into normalized embeddings (cosine-ready)."""
    model = get_model()
    return model.encode(
        texts, normalize_embeddings=True, show_progress_bar=False
    ).tolist()


def get_collection():
    """Open the persisted ChromaDB collection (cosine distance)."""
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=DB_PATH)
        _collection = client.get_or_create_collection(
            name=COLLECTION, metadata={"hnsw:space": "cosine"}
        )
    return _collection


def build_index():
    """Embed every chunk and (re)load it into ChromaDB with source metadata."""
    with open(CHUNKS_PATH, encoding="utf-8") as fh:
        chunks = json.load(fh)

    # fresh build so re-runs don't duplicate vectors
    client = chromadb.PersistentClient(path=DB_PATH)
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    collection = client.get_or_create_collection(
        name=COLLECTION, metadata={"hnsw:space": "cosine"}
    )
    global _collection
    _collection = collection

    # per-document position (needed for source attribution in later milestones)
    position = {}
    ids, docs, metas = [], [], []
    for c in chunks:
        src = c["source"]
        pos = position.get(src, 0)
        position[src] = pos + 1
        ids.append(c["id"])
        docs.append(c["text"])
        # ChromaDB metadata must be str/int/float/bool (no None)
        meta = {
            "source": src,
            "position": pos,
            "type": c.get("type", ""),
            "unit": c.get("unit", ""),
            "professor": c.get("professor") or "",
            "course": c.get("course") or "",
            "n_tokens": c.get("n_tokens", 0),
        }
        metas.append(meta)

    print(f"[embed] embedding {len(docs)} chunks with {MODEL_NAME}...")
    embeddings = embed(docs)

    collection.add(ids=ids, embeddings=embeddings, documents=docs, metadatas=metas)
    print(f"[store] added {collection.count()} vectors to '{COLLECTION}' at {DB_PATH}/")
    return collection


def retrieve(query, k=TOP_K):
    """Return the top-k most relevant chunks for a query.

    Returns a list of dicts: {text, source, position, professor, course, unit, distance}.
    """
    collection = get_collection()
    q_emb = embed([query])
    res = collection.query(
        query_embeddings=q_emb,
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    hits = []
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        hits.append({
            "text": doc,
            "distance": dist,
            "source": meta.get("source"),
            "position": meta.get("position"),
            "professor": meta.get("professor"),
            "course": meta.get("course"),
            "unit": meta.get("unit"),
        })
    return hits


# ------------------------------------------------------------------------------------------
# Evaluation harness — run the 5 planning.md test questions and print results + distances.
# ------------------------------------------------------------------------------------------
EVAL_QUERIES = [
    "Who teaches CS 135 at UNR?",
    "Is attendance mandatory for CS219 in Bashira Akter's course?",
    "What is the overall quality of Erin Keith on Rate My Professors?",
    "What is the level of difficulty in a course with Sara Davis?",
    "What percent of students would take Papachristos again?",
]


def run_eval():
    print("\n" + "=" * 90)
    print(f"RETRIEVAL TEST — top-{TOP_K} per query (cosine distance, lower = closer)")
    print("=" * 90)
    for q in EVAL_QUERIES:
        print(f"\n### QUERY: {q}")
        hits = retrieve(q, k=TOP_K)
        best = hits[0]["distance"]
        flag = "OK (<0.5)" if best < 0.5 else "WEAK (>=0.5) — inspect"
        print(f"    best distance = {best:.3f}  [{flag}]")
        for rank, h in enumerate(hits, 1):
            preview = h["text"].replace("\n", " ")
            if len(preview) > 160:
                preview = preview[:160] + "..."
            print(f"  {rank}. dist={h['distance']:.3f}  src={h['source']}#{h['position']} "
                  f"({h['unit']})\n     {preview}")


if __name__ == "__main__":
    if not os.path.exists(CHUNKS_PATH):
        raise SystemExit("data/chunks.json not found — run src/ingest_chunk.py first.")
    build_index()
    run_eval()
