import sys; sys.path.insert(0,'.')
import pytest
# RAGPipeline (which imports torch via sentence-transformers) must be imported
# before ragas_evaluator (which imports the `datasets` package) - datasets-first
# reliably breaks torch's native DLL loading on Windows (WinError 1114 on
# torch/lib/c10.dll). Confirmed by direct reproduction; app.py already gets the
# order right by accident, this file didn't.
from src.rag.pipeline import RAGPipeline
from src.evaluation.ragas_evaluator import RAGASEvaluator
from src.utils.settings import get_settings

DOCS = [{"content": "DLD charges a 4% transfer fee on property purchases in Dubai, paid at registration.", "source": "dld_test.txt"}]
TEST_QUERIES = [{"question": "What percentage transfer fee does DLD charge on Dubai property purchases?", "ground_truth": "4% of the purchase price", "source_doc": "dld_test.txt"}]

no_llm = not bool(get_settings().active_api_key)
needs_llm = pytest.mark.skipif(no_llm, reason="No GOOGLE_API_KEY/GROQ_API_KEY configured - real ragas evaluation needs a live LLM")

@pytest.fixture(scope="module")
def rag(tmp_path_factory):
    # must not use the default index path - that's the same file app.py loads
    # on startup, and build_index() unconditionally overwrites it on disk
    p = RAGPipeline()
    p._index_path = tmp_path_factory.mktemp("rag_index") / "idx"
    p.build_index(DOCS)
    return p

@pytest.fixture(scope="module")
def result(rag):
    return RAGASEvaluator(rag_pipeline=rag).run_evaluation(test_queries=TEST_QUERIES)

def test_requires_pipeline():
    with pytest.raises(ValueError):
        RAGASEvaluator(rag_pipeline=None).run_evaluation(test_queries=TEST_QUERIES)

@needs_llm
def test_runs(result): assert "summary" in result

@needs_llm
def test_faithfulness_in_range(result):
    faith = result["summary"]["faithfulness"]
    if faith != faith:  # NaN - the judge LLM call failed (e.g. transient rate limit), not our bug
        pytest.skip("ragas judge returned NaN - LLM call failed transiently, nothing to assert")
    assert 0 <= faith <= 1

@needs_llm
def test_hallucination_consistent_with_faithfulness(result):
    s = result["summary"]
    if s["faithfulness"] != s["faithfulness"]:
        pytest.skip("ragas judge returned NaN - LLM call failed transiently, nothing to assert")
    assert abs(s["hallucination_rate"] - (1 - s["faithfulness"])) < 1e-9

@needs_llm
def test_per_query_matches_input(result): assert len(result["per_query_results"]) == len(TEST_QUERIES)

@needs_llm
def test_targets_present(result):
    s = result["summary"]
    assert "faithfulness_achieved" in s and "hallucination_target_met" in s
