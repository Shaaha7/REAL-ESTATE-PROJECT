import sys; sys.path.insert(0,'.')
from src.evaluation.ragas_evaluator import RAGASEvaluator

def test_runs(): r=RAGASEvaluator().run_evaluation(); assert "summary" in r
def test_faithfulness(): r=RAGASEvaluator().run_evaluation(); assert 0<=r["summary"]["faithfulness"]<=1
def test_hallucination(): r=RAGASEvaluator().run_evaluation(); assert r["summary"]["hallucination_rate"]<0.1
def test_per_query(): r=RAGASEvaluator().run_evaluation(); assert len(r["per_query_results"])>=5
def test_targets(): r=RAGASEvaluator().run_evaluation(); s=r["summary"]; assert "faithfulness_achieved" in s and "hallucination_target_met" in s
