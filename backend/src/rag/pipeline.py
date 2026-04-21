from __future__ import annotations
import hashlib, pickle
from pathlib import Path
from typing import Optional
import faiss, numpy as np
from loguru import logger
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder
from src.utils.settings import get_settings
from src.utils.llm_client import LLMClient
from src.prompts.templates import build_rag_prompt

class Document:
    def __init__(self, doc_id: str, content: str, metadata: dict | None = None):
        self.doc_id = doc_id; self.content = content; self.metadata = metadata or {}
    def to_dict(self): return {"doc_id":self.doc_id,"content":self.content,"metadata":self.metadata}

class RAGPipeline:
    def __init__(self):
        self.settings = get_settings(); self.llm = LLMClient()
        self._embedder: Optional[SentenceTransformer] = None
        self._reranker: Optional[CrossEncoder] = None
        self._index: Optional[faiss.IndexFlatIP] = None
        self._docs: list[Document] = []; self._bm25: Optional[BM25Okapi] = None
        self._index_path = Path(self.settings.faiss_index_path)

    @property
    def embedder(self):
        if not self._embedder:
            logger.info(f"Loading embedder: {self.settings.embedding_model}")
            self._embedder = SentenceTransformer(self.settings.embedding_model)
        return self._embedder

    @property
    def reranker(self):
        if not self._reranker:
            self._reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        return self._reranker

    def _chunk(self, text: str, source: str) -> list[Document]:
        size = self.settings.chunk_size * 4; overlap = self.settings.chunk_overlap * 4
        chunks, start, idx = [], 0, 0
        while start < len(text):
            end = min(start+size, len(text))
            doc_id = hashlib.md5(f"{source}:{idx}".encode()).hexdigest()[:12]
            chunks.append(Document(doc_id, text[start:end], {"source":source,"chunk_idx":idx}))
            start += size - overlap; idx += 1
        return chunks

    def build_index(self, documents: list[dict]) -> None:
        logger.info(f"Building index from {len(documents)} docs…")
        all_chunks = [c for d in documents for c in self._chunk(d["content"], d.get("source","doc"))]
        self._docs = all_chunks; texts = [d.content for d in all_chunks]
        embs = self.embedder.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False).astype(np.float32)
        self._index = faiss.IndexFlatIP(embs.shape[1]); self._index.add(embs)
        self._bm25 = BM25Okapi([t.lower().split() for t in texts])
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(self._index_path)+".faiss")
        with open(str(self._index_path)+".meta.pkl","wb") as f: pickle.dump(self._docs,f)
        logger.success(f"Index built: {len(all_chunks)} chunks")

    def load_index(self) -> bool:
        fp = str(self._index_path)+".faiss"; mp = str(self._index_path)+".meta.pkl"
        if not Path(fp).exists(): return False
        self._index = faiss.read_index(fp)
        with open(mp,"rb") as f: self._docs = pickle.load(f)
        self._bm25 = BM25Okapi([d.content.lower().split() for d in self._docs])
        logger.success(f"Index loaded: {len(self._docs)} chunks")
        return True

    def _dense(self, query: str, k: int = 10):
        k = min(k, max(1, len(self._docs)))
        q = self.embedder.encode([query], normalize_embeddings=True).astype(np.float32)
        scores, idxs = self._index.search(q, k)
        return [(self._docs[i], float(s)) for s,i in zip(scores[0],idxs[0]) if 0<=i<len(self._docs) and s>=self.settings.min_score_threshold]

    def _sparse(self, query: str, k: int = 10):
        sc = self._bm25.get_scores(query.lower().split())
        top = np.argsort(sc)[::-1][:k]
        return [(self._docs[i], float(sc[i])) for i in top if sc[i]>0]

    def _merge(self, dense, sparse, alpha: float = 0.6):
        scores: dict = {}; dm: dict = {}
        for rank,(doc,_) in enumerate(dense): scores[doc.doc_id]=scores.get(doc.doc_id,0)+alpha/(rank+1); dm[doc.doc_id]=doc
        for rank,(doc,_) in enumerate(sparse): scores[doc.doc_id]=scores.get(doc.doc_id,0)+(1-alpha)/(rank+1); dm[doc.doc_id]=doc
        return [(dm[did],scores[did]) for did in sorted(scores,key=lambda x:scores[x],reverse=True)]

    def _rerank(self, query: str, cands, top_k: int = 5):
        if not cands: return []
        ce = self.reranker.predict([(query, doc.content) for doc,_ in cands])
        ranked = sorted(zip(cands,ce),key=lambda x:x[1],reverse=True)
        return [(doc,float(s)) for (doc,_),s in ranked[:top_k]]

    def query(self, question: str) -> dict:
        if self._index is None:
            if not self.load_index():
                return {"answer":"Knowledge base not indexed. Index will be built on startup with real documents.","sources":[],"confidence":0.0,"answer_found_in_context":False}
        dense = self._dense(question); sparse = self._sparse(question)
        merged = self._merge(dense, sparse)
        top_k = self._rerank(question, merged, self.settings.top_k_final)
        if not top_k:
            return {"answer":"No relevant documents found for this query.","sources":[],"confidence":0.0,"answer_found_in_context":False}
        context = "\n\n---\n\n".join(f"[{doc.doc_id}] (source: {doc.metadata.get('source','?')}) {doc.content}" for doc,_ in top_k)
        result = self.llm.invoke(build_rag_prompt(context), question, expect_json=True)
        if isinstance(result,dict):
            result["retrieved_chunks"]=[doc.doc_id for doc,_ in top_k]
            result["rerank_scores"]=[round(s,4) for _,s in top_k]
        return result

    def load_documents_from_dir(self, dir_path: str) -> int:
        """Load all .txt files from a directory into the index."""
        p = Path(dir_path); docs = []
        for txt_file in sorted(p.glob("**/*.txt")):
            content = txt_file.read_text(encoding="utf-8", errors="ignore")
            if content.strip():
                docs.append({"content": content, "source": txt_file.name})
        if docs:
            self.build_index(docs)
            logger.success(f"Indexed {len(docs)} documents from {dir_path}")
        return len(docs)
