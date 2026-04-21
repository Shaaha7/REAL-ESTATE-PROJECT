"""
UPDATED app.py startup section — replace the lifespan function in your app.py
Key change: loads ALL documents from ALL subdirectories on startup, forces rebuild if new docs added

Find this in your app.py:
  @asynccontextmanager
  async def lifespan(app: FastAPI):

Replace the entire lifespan function with this:
"""

# ─── PASTE THIS INTO app.py replacing the existing lifespan function ──────────

LIFESPAN_CODE = '''
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _lead, _property, _rag, _orch
    logger.info("="*55 + "\\n  PropAI Platform — Starting Up\\n" + "="*55)

    # Lead scoring — train on 3000-record synthetic dataset
    _lead = LeadScoringAgent()
    _ = _lead.model  # triggers training if model not found

    # Property retrieval
    _property = PropertyRetrievalAgent()

    # RAG Pipeline — load ALL documents from ALL subdirectories
    _rag = RAGPipeline()
    index_loaded = _rag.load_index()

    if not index_loaded:
        logger.info("No existing index — building from all documents...")
        n = _rag.rebuild_from_all_docs()
        logger.success(f"Index built: {n} documents")
    else:
        # Check if we have new documents that are not yet indexed
        all_txt_files = list(Path("data/documents").glob("**/*.txt"))
        if len(all_txt_files) > 0:
            # Count existing chunks vs expected
            existing_chunks = len(_rag._docs)
            expected_min_chunks = len(all_txt_files) * 2  # at least 2 chunks per doc
            if existing_chunks < expected_min_chunks:
                logger.info(f"Index may be stale ({existing_chunks} chunks for {len(all_txt_files)} docs). Rebuilding...")
                n = _rag.rebuild_from_all_docs()
                logger.success(f"Index rebuilt: {n} documents")

    # Orchestrator
    _orch = OrchestratorAgent()

    logger.success(
        f"All agents ready ✓\\n"
        f"  Provider: {settings.llm_provider} | Model: {settings.active_model}\\n"
        f"  RAG chunks: {len(_rag._docs)} | Documents: {len(list(Path('data/documents').glob('**/*.txt')))}\\n"
        f"  API key configured: {bool(settings.active_api_key)}"
    )
    yield
'''

# ─── ALSO ADD this new endpoint to app.py ─────────────────────────────────────

NEW_ENDPOINT = '''
@app.post("/api/rag/rebuild", tags=["RAG"])
async def rebuild_rag_index():
    """Force rebuild the RAG index from all documents in data/documents directory."""
    if not _rag:
        raise HTTPException(503, "RAG not ready")
    n = _rag.rebuild_from_all_docs()
    return {
        "status": "rebuilt",
        "documents_indexed": n,
        "chunks_total": len(_rag._docs)
    }
'''

print("Instructions:")
print("1. In backend/src/rag/pipeline.py — replace entire file with rag_pipeline_updated.py")
print("2. In backend/src/prompts/templates.py — replace entire file with prompts_updated.py")
print("3. In backend/app.py — replace lifespan function with LIFESPAN_CODE above")
print("4. In backend/app.py — add NEW_ENDPOINT after existing /api/rag/index endpoint")
print("5. Copy all .txt files from data/documents/ folders into your project")
print("6. Restart the backend — it will auto-rebuild the index with all new documents")
