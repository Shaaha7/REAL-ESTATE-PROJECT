"""
Builds a real RAGAS test-query set from the actual knowledge-base and
brochure documents, replacing the old 5-15 hand-written query stub.

For each source document, asks the configured LLM to write factual
questions answerable from that document plus a concise ground-truth
answer extracted from the text. This is the same general approach RAGAS's
own testset generator uses (LLM-grounded question synthesis from source
documents) - the point is a query set wide enough to cover the corpus,
not hand-picked queries that flatter the retriever.

Run from backend/:
    python scripts/generate_ragas_testset.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
from src.utils.llm_client import LLMClient  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parent.parent
DOC_DIRS = ["data/documents/rag_knowledge", "data/documents/brochures"]
QUESTIONS_PER_DOC = 3
SKIP_FILENAMES = {"00_PORTFOLIO_INDEX.txt"}  # index file, not real content

GEN_SYSTEM = """You write evaluation questions for a RAG system testing a Dubai real estate knowledge base.
Given a source document, produce exactly {n} factual questions that are answerable using ONLY the given document, each paired with a concise ground-truth answer copied/derived directly from the text (not from outside knowledge).
Vary the questions - cover different facts/sections of the document, not the same fact reworded.
Respond ONLY with a JSON array: [{{"question": "...", "ground_truth": "..."}}, ...]"""


def load_source_docs() -> list[dict]:
    docs = []
    for d in DOC_DIRS:
        p = BACKEND_DIR / d
        if not p.exists():
            continue
        for f in sorted(p.glob("*.txt")):
            if f.name in SKIP_FILENAMES:
                continue
            content = f.read_text(encoding="utf-8", errors="ignore").strip()
            if content:
                docs.append({"source": f.name, "content": content})
    return docs


def generate_queries_for_doc(llm: LLMClient, doc: dict, n: int) -> list[dict]:
    system = GEN_SYSTEM.format(n=n)
    result = llm.invoke(system, doc["content"][:6000], expect_json=True)
    items = result if isinstance(result, list) else result.get("questions") if isinstance(result, dict) else None
    if not isinstance(items, list):
        print(f"  WARN: could not parse questions for {doc['source']}, got: {str(result)[:200]}")
        return []
    out = []
    for it in items:
        if isinstance(it, dict) and it.get("question") and it.get("ground_truth"):
            out.append({"question": it["question"].strip(), "ground_truth": it["ground_truth"].strip(), "source_doc": doc["source"]})
    return out


def main():
    llm = LLMClient()
    if not llm.langchain_llm:
        print("ERROR: no LLM configured (check backend/.env GOOGLE_API_KEY / GROQ_API_KEY). Aborting.")
        sys.exit(1)

    docs = load_source_docs()
    print(f"Found {len(docs)} source documents. Generating {QUESTIONS_PER_DOC} questions each...")

    all_queries = []
    for i, doc in enumerate(docs, start=1):
        qs = generate_queries_for_doc(llm, doc, QUESTIONS_PER_DOC)
        print(f"  [{i}/{len(docs)}] {doc['source']}: {len(qs)} questions")
        all_queries.extend(qs)

    out_path = BACKEND_DIR / "data/evaluation/ragas_test_queries.json"
    out_path.write_text(json.dumps(all_queries, indent=2))
    print(f"\nWrote {len(all_queries)} queries across {len(docs)} documents to {out_path.relative_to(BACKEND_DIR)}")


if __name__ == "__main__":
    main()
