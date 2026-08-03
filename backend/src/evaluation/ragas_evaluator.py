from __future__ import annotations
import json
from pathlib import Path

from datasets import Dataset
from langchain_community.embeddings import HuggingFaceEmbeddings
from loguru import logger
from ragas import evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness
from ragas.run_config import RunConfig

from src.utils.settings import get_settings


class RAGASEvaluator:
    """Runs the real ragas library against a live RAGPipeline. Requires a
    configured LLM (used both to generate RAG answers and, wrapped for ragas,
    as the faithfulness/relevancy judge) - there is no offline/fake mode."""

    # Free-tier LLM rate limits mean individual ragas metric calls routinely
    # time out and land as NaN even when the overall evaluate() call "succeeds".
    # A mean over 1 surviving value out of 9 is not a measurement - gate the
    # achieved/met flags on an actual minimum sample surviving per metric.
    MIN_VALID_SAMPLE = 5

    def __init__(self, rag_pipeline=None):
        self.rag = rag_pipeline
        self.results_path = Path("data/evaluation/ragas_results.json")
        self.results_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_test_queries(self) -> list[dict]:
        p = Path("data/evaluation/ragas_test_queries.json")
        if not p.exists():
            raise FileNotFoundError(
                "No test query set at data/evaluation/ragas_test_queries.json. "
                "Run scripts/generate_ragas_testset.py first."
            )
        with open(p) as f:
            return json.load(f)

    def run_evaluation(self, test_queries: list[dict] | None = None) -> dict:
        if self.rag is None:
            raise ValueError("RAGASEvaluator requires a live rag_pipeline (it generates the answers/contexts being graded).")
        if not self.rag.llm.langchain_llm:
            raise RuntimeError("No LLM configured (GOOGLE_API_KEY / GROQ_API_KEY missing) - cannot generate answers or run the ragas judge.")

        queries = test_queries or self._load_test_queries()
        logger.info(f"RAGAS evaluation: running RAG pipeline over {len(queries)} queries")

        questions, answers, contexts_list, ground_truths, skipped = [], [], [], [], 0
        for q in queries:
            try:
                r = self.rag.query(q["question"])
            except Exception as e:
                logger.warning(f"RAG query failed for '{q['question'][:60]}': {e}")
                skipped += 1
                continue
            answer = r.get("answer") if isinstance(r, dict) else None
            contexts = r.get("contexts") if isinstance(r, dict) else None
            if not answer or not contexts:
                skipped += 1
                continue
            questions.append(q["question"])
            answers.append(answer)
            contexts_list.append(contexts)
            ground_truths.append(q.get("ground_truth", ""))

        if not questions:
            raise RuntimeError("RAG pipeline produced no usable answers/contexts for any query - nothing to evaluate.")

        dataset = Dataset.from_dict({
            "question": questions,
            "answer": answers,
            "contexts": contexts_list,
            "ground_truth": ground_truths,
        })

        settings = get_settings()
        judge_llm = LangchainLLMWrapper(self.rag.llm.langchain_llm)
        judge_embeddings = LangchainEmbeddingsWrapper(HuggingFaceEmbeddings(model_name=settings.embedding_model))

        logger.info(f"Running ragas.evaluate() on {len(questions)} queries (judge: {settings.llm_provider}/{settings.active_model})")
        # Free-tier LLM APIs (Groq/Gemini) rate-limit hard; ragas defaults to 16
        # concurrent workers, which reliably trips them. 2 workers with generous
        # per-call timeout/wait trades speed for actually finishing.
        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
            llm=judge_llm,
            embeddings=judge_embeddings,
            raise_exceptions=False,
            run_config=RunConfig(max_workers=2, timeout=90, max_wait=90),
        )
        df = result.to_pandas()

        cols = ["question", "answer", "faithfulness", "answer_relevancy", "context_precision", "context_recall"]
        per_query = df[cols].to_dict(orient="records")

        def safe_mean(col: str) -> tuple[float, int]:
            s = df[col].dropna()
            return (float(s.mean()) if len(s) else float("nan")), len(s)

        faith, faith_n = safe_mean("faithfulness")
        ar, ar_n = safe_mean("answer_relevancy")
        cp, cp_n = safe_mean("context_precision")
        cr, cr_n = safe_mean("context_recall")
        hallucination_rate = (1 - faith) if faith == faith else float("nan")
        enough_signal = faith_n >= self.MIN_VALID_SAMPLE
        summary = {
            "faithfulness": faith,
            "answer_relevancy": ar,
            "context_precision": cp,
            "context_recall": cr,
            "hallucination_rate": hallucination_rate,
            "num_queries": len(questions),
            "num_skipped": skipped,
            # how many of num_queries actually produced a non-NaN score for each
            # metric - ragas silently NaNs a row when its judge call times out,
            # which a plain dropna().mean() would hide
            "valid_sample_sizes": {
                "faithfulness": faith_n, "answer_relevancy": ar_n,
                "context_precision": cp_n, "context_recall": cr_n,
            },
            "min_valid_sample_required": self.MIN_VALID_SAMPLE,
            "target_faithfulness": 0.97,
            "target_hallucination_rate": 0.02,
            "faithfulness_achieved": bool(faith == faith and faith >= 0.97 and enough_signal),
            "hallucination_target_met": bool(hallucination_rate == hallucination_rate and hallucination_rate <= 0.02 and enough_signal),
            "insufficient_sample": not enough_signal,
        }
        results = {"summary": summary, "per_query_results": per_query}
        self.results_path.write_text(json.dumps(results, indent=4, default=str))
        if enough_signal:
            logger.success(f"RAGAS: faithfulness={faith:.4f} over {faith_n}/{len(questions)} queries with a valid score ({skipped} skipped upstream)")
        else:
            logger.warning(f"RAGAS: only {faith_n}/{len(questions)} queries produced a valid faithfulness score (below MIN_VALID_SAMPLE={self.MIN_VALID_SAMPLE}) - likely judge-LLM rate limiting, not a real measurement")
        return results
