import sys; sys.path.insert(0,'.')
import pytest
from pathlib import Path
from src.rag.pipeline import RAGPipeline,Document

DOCS=[{"content":"DLD charges 4% transfer fee on property purchases in Dubai.","source":"dld.txt"},{"content":"Minimum 25% down payment required for expat mortgages in UAE.","source":"mortgage.txt"},{"content":"Golden Visa requires AED 2 million property investment, fully paid.","source":"visa.txt"}]

def test_chunk(): p=RAGPipeline(); c=p._chunk("A"*5000,"test.txt"); assert len(c)>=2
def test_build(tmp_path):
    p=RAGPipeline(); p._index_path=tmp_path/"idx"; p.build_index(DOCS)
    assert p._index is not None; assert len(p._docs)>=len(DOCS)
def test_query_no_index():
    p=RAGPipeline(); p._index_path=Path("/nonexistent/faiss_index")
    r=p.query("What is DLD fee?"); assert "answer" in r
def test_document(): d=Document("abc","Real estate content",{"source":"s.txt"}); assert d.to_dict()["doc_id"]=="abc"
def test_dense_retrieve(tmp_path):
    p=RAGPipeline(); p._index_path=tmp_path/"idx"; p.build_index(DOCS)
    r=p._dense("DLD fees Dubai",k=3); assert isinstance(r,list)
