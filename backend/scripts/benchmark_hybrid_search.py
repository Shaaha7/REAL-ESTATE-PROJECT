"""
Benchmarks FAISS-only (dense) retrieval against the production FAISS+BM25+
cross-encoder hybrid pipeline, measuring top-3 retrieval accuracy: for each
test question, is the document it was generated from present among the
top-3 retrieved chunks' source files?

Reuses data/evaluation/ragas_test_queries.json - each entry already records
which source document it was generated from (source_doc), which is exactly
the ground truth a retrieval benchmark needs. Run generate_ragas_testset.py
first if that file doesn't exist yet.

Run from backend/:
    python scripts/benchmark_hybrid_search.py

Reports whatever the data shows. Not tuned toward any target percentage.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
from src.rag.pipeline import RAGPipeline  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parent.parent
DOC_DIRS = ["data/documents/rag_knowledge", "data/documents/brochures"]
TOP_K = 3


def build_fresh_index() -> RAGPipeline:
    rag = RAGPipeline()
    docs = []
    for d in DOC_DIRS:
        p = BACKEND_DIR / d
        for f in sorted(p.glob("*.txt")):
            content = f.read_text(encoding="utf-8", errors="ignore").strip()
            if content:
                docs.append({"content": content, "source": f.name})
    print(f"Building fresh index from {len(docs)} documents...")
    rag.build_index(docs)
    return rag


def dense_only_top_k(rag: RAGPipeline, question: str, k: int) -> list[str]:
    hits = rag._dense(question, k=k)
    return [doc.metadata.get("source", "?") for doc, _ in hits]


def hybrid_top_k(rag: RAGPipeline, question: str, k: int) -> list[str]:
    dense = rag._dense(question, k=10)
    sparse = rag._sparse(question, k=10)
    merged = rag._merge(dense, sparse)
    reranked = rag._rerank(question, merged, top_k=k)
    return [doc.metadata.get("source", "?") for doc, _ in reranked]


def main():
    queries_path = BACKEND_DIR / "data/evaluation/ragas_test_queries.json"
    if not queries_path.exists():
        print(f"ERROR: {queries_path} not found. Run generate_ragas_testset.py first.")
        sys.exit(1)
    queries = json.loads(queries_path.read_text())
    queries = [q for q in queries if q.get("source_doc")]
    print(f"Loaded {len(queries)} queries with known source documents.\n")

    rag = build_fresh_index()

    dense_hits = 0
    hybrid_hits = 0
    per_query = []
    for i, q in enumerate(queries, start=1):
        question, expected_source = q["question"], q["source_doc"]

        dense_sources = dense_only_top_k(rag, question, TOP_K)
        hybrid_sources = hybrid_top_k(rag, question, TOP_K)

        dense_hit = expected_source in dense_sources
        hybrid_hit = expected_source in hybrid_sources
        dense_hits += dense_hit
        hybrid_hits += hybrid_hit

        per_query.append({
            "question": question, "expected_source": expected_source,
            "dense_top3_sources": dense_sources, "dense_hit": dense_hit,
            "hybrid_top3_sources": hybrid_sources, "hybrid_hit": hybrid_hit,
        })
        flag = "" if dense_hit == hybrid_hit else "  <-- DIFFERS"
        print(f"  [{i}/{len(queries)}] dense={'HIT ' if dense_hit else 'miss'} hybrid={'HIT ' if hybrid_hit else 'miss'}{flag}  ({expected_source})")

    n = len(queries)
    dense_acc = dense_hits / n
    hybrid_acc = hybrid_hits / n
    abs_diff = hybrid_acc - dense_acc
    rel_diff = (abs_diff / dense_acc * 100) if dense_acc > 0 else float("inf")

    summary = {
        "n_queries": n, "top_k": TOP_K,
        "dense_only_top3_accuracy": dense_acc,
        "hybrid_top3_accuracy": hybrid_acc,
        "absolute_improvement_pct_points": abs_diff * 100,
        "relative_improvement_pct": rel_diff,
        "per_query": per_query,
    }
    out_path = BACKEND_DIR / "data/evaluation/hybrid_search_benchmark.json"
    out_path.write_text(json.dumps(summary, indent=2))

    print("\n" + "=" * 70)
    print(f"RESULTS (n={n} queries, top-{TOP_K} accuracy)")
    print("=" * 70)
    print(f"  FAISS-only (dense):        {dense_hits}/{n} = {dense_acc:.1%}")
    print(f"  FAISS+BM25+CrossEncoder:   {hybrid_hits}/{n} = {hybrid_acc:.1%}")
    print(f"  Absolute improvement:      {abs_diff*100:+.1f} percentage points")
    print(f"  Relative improvement:      {rel_diff:+.1f}%")
    print(f"\nFull results written to {out_path.relative_to(BACKEND_DIR)}")


if __name__ == "__main__":
    main()
