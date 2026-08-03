from __future__ import annotations
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
import secrets, time, uuid
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from loguru import logger
from pydantic import BaseModel, Field
from src.utils.settings import get_settings
# torch (via RAGPipeline's sentence-transformers embedder) must import before
# xgboost (via LeadScoringAgent) - on Windows, loading xgboost's native DLL
# first reliably breaks torch's own DLL init (WinError 1114 on torch/lib/
# c10.dll). Same class of issue as the documented torch-vs-datasets ordering
# conflict; confirmed by direct reproduction in this environment.
from src.rag.pipeline import RAGPipeline
from src.agents.lead_scoring_agent import LeadScoringAgent, LeadData
from src.agents.property_retrieval_agent import PropertyRetrievalAgent, PropertyQuery, DEMO_PROPERTIES
from src.agents.orchestrator import OrchestratorAgent
from src.evaluation.ragas_evaluator import RAGASEvaluator

settings = get_settings()

# Console sink (loguru's default) stays for local dev visibility. These two
# add real file-based logging: a human-readable rotating log, and a JSON-lines
# sink suitable for a real log pipeline (Loki/ELK/CloudWatch etc. all ingest
# JSON-per-line naturally). Previously loguru only ever wrote to stdout - if
# the process wasn't attached to a terminal, there was no record at all.
Path("logs").mkdir(exist_ok=True)
logger.add("logs/app.log", level=settings.log_level, rotation="10 MB", retention="7 days", compression="zip")
logger.add("logs/app.jsonl", level=settings.log_level, rotation="10 MB", retention="7 days", serialize=True)

_lead=_property=_rag=_orch=None
_request_latencies_ms: deque = deque(maxlen=1000)  # real observed latencies, this process only
_request_count = 0
_error_count = 0
_server_start_time = time.time()

# Admin key protects the two endpoints that mutate the knowledge base
# (POST /api/rag/index, /api/rag/rebuild). If ADMIN_API_KEY isn't set, generate
# one at startup and log it - keeps the app usable with zero config (matching
# every other "works without extra setup" default here) while still requiring
# a real key instead of leaving these open to anyone.
_ADMIN_API_KEY = settings.admin_api_key or secrets.token_urlsafe(24)
if not settings.admin_api_key:
    logger.warning(f"ADMIN_API_KEY not set - generated one for this run: {_ADMIN_API_KEY}")
    logger.warning("Set ADMIN_API_KEY in .env to keep a stable key across restarts.")

async def require_admin_key(x_api_key: str = Header(default="")):
    if not secrets.compare_digest(x_api_key, _ADMIN_API_KEY):
        raise HTTPException(401, "Missing or invalid X-API-Key header")

# Simple in-memory sliding-window limiter, per client IP, for the LLM-backed
# endpoints (the ones that cost real money/quota per call). Single-process
# only - fine for this app's scale, would need a shared store (e.g. the same
# Redis RAGCache already falls back from) behind more than one worker.
_rate_limit_hits: dict[str, deque] = {}

async def rate_limit_dep(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = _rate_limit_hits.setdefault(client_ip, deque())
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= settings.rate_limit_per_minute:
        raise HTTPException(429, f"Rate limit exceeded ({settings.rate_limit_per_minute}/min). Try again shortly.")
    window.append(now)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _lead,_property,_rag,_orch
    logger.info("="*55+"\n  PropAI Platform — Starting Up\n"+"="*55)
    _lead=LeadScoringAgent(); _=_lead.model
    _property=PropertyRetrievalAgent()
    _rag=RAGPipeline()
    if not _rag.load_index():
        logger.info("Building RAG index from documents…")
        _rag.rebuild_from_all_docs()
    _orch=OrchestratorAgent()
    logger.success(f"All agents ready ✓ | Provider: {settings.llm_provider} | RAG chunks: {len(_rag._docs)}")
    yield

app = FastAPI(title="PropAI — Real Estate AI Platform", version="1.0.0", lifespan=lifespan, docs_url="/api/docs", redoc_url="/api/redoc", openapi_url="/api/openapi.json")
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(CORSMiddleware, allow_origins=list({settings.frontend_url,"http://localhost:3000","http://localhost:5173"}), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.middleware("http")
async def latency_header(request, call_next):
    global _request_count, _error_count
    t0=time.perf_counter(); response=await call_next(request)
    ms = round((time.perf_counter()-t0)*1000,2)
    response.headers["X-Latency-MS"]=str(ms)
    if request.url.path.startswith("/api"):
        _request_latencies_ms.append(ms); _request_count += 1
        if response.status_code>=400: _error_count += 1
    return response

class AgentRequest(BaseModel):
    message: str=Field(...,min_length=1,max_length=2000)
    session_id: str=Field(default_factory=lambda:str(uuid.uuid4()))
class RAGRequest(BaseModel):
    question: str=Field(...,min_length=3,max_length=500)
class LeadScoreRequest(BaseModel):
    lead_id: str=Field(default_factory=lambda:str(uuid.uuid4()))
    client_name: str; budget_aed: float=Field(0.0,ge=0); property_type: str="apartment"
    location_preference: str=""; bedrooms: Optional[int]=None; timeline_months: Optional[int]=None
    num_interactions: int=Field(0,ge=0); avg_response_hours: float=Field(24.0,ge=0)
    message_quality_score: float=Field(0.5,ge=0,le=1); source: str="web"
class PropertySearchRequest(BaseModel):
    property_type: Optional[str]=None; location: Optional[str]=None
    budget_min: Optional[float]=None; budget_max: Optional[float]=None; bedrooms: Optional[int]=None; free_text: str=""
class IndexRequest(BaseModel):
    documents: list[dict]

@app.get("/api", tags=["Health"])
async def root(): return {"service":"PropAI Real Estate Platform","version":"1.0.0","status":"running","docs":"/api/docs","provider":settings.llm_provider,"model":settings.active_model}

@app.get("/api/health", tags=["Health"])
async def health(): return {"status":"healthy","agents":{"orchestrator":_orch is not None,"lead_scoring":_lead is not None,"property_retrieval":_property is not None,"rag_pipeline":_rag is not None},"rag_chunks":len(_rag._docs) if _rag else 0,"provider":settings.llm_provider,"model":settings.active_model,"api_key_configured":bool(settings.active_api_key)}

@app.post("/api/agent/chat", tags=["Orchestrator"], dependencies=[Depends(rate_limit_dep)])
async def agent_chat(req: AgentRequest):
    if not _orch: raise HTTPException(503,"Orchestrator not ready")
    return _orch.run(req.message, session_id=req.session_id)

@app.post("/api/leads/score", tags=["Lead Scoring"], dependencies=[Depends(rate_limit_dep)])
async def score_lead(req: LeadScoreRequest):
    if not _lead: raise HTTPException(503,"Lead agent not ready")
    return _lead.score(LeadData(**req.model_dump())).model_dump()

@app.get("/api/leads/sample", tags=["Lead Scoring"])
async def get_sample_leads():
    import json
    p = Path("data/synthetic/leads_200.json")
    if p.exists():
        with open(p) as f: data=json.load(f)
        return {"leads":data[:50],"total":len(data)}
    return {"leads":[],"total":0}

@app.get("/api/properties", tags=["Properties"])
async def get_all_properties(): return {"properties":DEMO_PROPERTIES,"total":len(DEMO_PROPERTIES)}

@app.post("/api/properties/search", tags=["Properties"])
async def search_properties(req: PropertySearchRequest):
    if not _property: raise HTTPException(503,"Property agent not ready")
    return _property.retrieve(PropertyQuery(**req.model_dump()))

@app.get("/api/properties/{property_id}", tags=["Properties"])
async def get_property(property_id: str):
    prop=next((p for p in DEMO_PROPERTIES if p["id"]==property_id),None)
    if not prop: raise HTTPException(404,f"Property {property_id} not found")
    return prop

@app.post("/api/rag/query", tags=["RAG"], dependencies=[Depends(rate_limit_dep)])
async def rag_query(req: RAGRequest):
    if not _rag: raise HTTPException(503,"RAG not ready")
    return _rag.query(req.question)

@app.post("/api/rag/index", tags=["RAG"], dependencies=[Depends(require_admin_key)])
async def build_index(req: IndexRequest):
    if not _rag: raise HTTPException(503,"RAG not ready")
    if len(req.documents) > 200:
        raise HTTPException(413, "Too many documents in one request (max 200)")
    _rag.build_index(req.documents); return {"status":"indexed","chunks_indexed":len(_rag._docs)}

@app.get("/api/rag/documents", tags=["RAG"])
async def list_documents():
    docs = []
    for d in ["data/documents/rag_knowledge","data/documents/brochures"]:
        p=Path(d)
        if p.exists(): docs.extend([{"name":f.name,"size":f.stat().st_size,"dir":d} for f in sorted(p.glob("*.txt"))])
    return {"documents":docs,"total":len(docs)}

@app.get("/api/evaluation/ragas", tags=["Evaluation"])
async def ragas_eval(): return RAGASEvaluator(rag_pipeline=_rag).run_evaluation()

@app.get("/api/metrics", tags=["Observability"])
async def metrics():
    lat = list(_request_latencies_ms)
    lat_sorted = sorted(lat)
    def _pct(p: float) -> Optional[float]:
        if not lat_sorted: return None
        idx = min(len(lat_sorted)-1, int(len(lat_sorted)*p))
        return lat_sorted[idx]
    return {"rag_chunks":len(_rag._docs) if _rag else 0,"lead_model_loaded":_lead is not None,
            "provider":settings.llm_provider,"model":settings.active_model,"api_key_configured":bool(settings.active_api_key),
            "requests_total":_request_count,"errors_total":_error_count,
            "error_rate_pct":round(_error_count/_request_count*100,2) if _request_count else 0.0,
            "uptime_seconds":round(time.time()-_server_start_time,1),
            "latency_ms":{"avg":round(sum(lat)/len(lat),1) if lat else None,"p50":_pct(0.50),"p95":_pct(0.95),"p99":_pct(0.99),"samples":len(lat)}}

@app.get("/api/stats/dashboard", tags=["Dashboard"])
async def dashboard_stats():
    import json
    from datetime import date
    leads_path=Path("data/synthetic/leads_200.json")
    hot=warm=cold=0
    lead_conversion_rate=avg_lead_score=revenue_pipeline_aed=deals_closed_this_month=0
    if leads_path.exists():
        with open(leads_path) as f: leads=json.load(f)
        hot=sum(1 for l in leads if l["tier"]=="HOT"); warm=sum(1 for l in leads if l["tier"]=="WARM"); cold=sum(1 for l in leads if l["tier"]=="COLD")
        closed=[l for l in leads if l.get("status")=="closed"]
        active=[l for l in leads if l.get("status") not in ("closed","lost")]
        lead_conversion_rate=round(len(closed)/len(leads)*100,1) if leads else 0
        avg_lead_score=round(sum(l.get("lead_score",0) for l in leads)/len(leads),1) if leads else 0
        revenue_pipeline_aed=sum(l.get("budget_aed",0) for l in active)
        # "this month" = the most recent calendar month present in the dataset's own
        # last_contact dates, not the real wall-clock month (the dates are static synthetic data)
        contact_dates=[l.get("last_contact") for l in leads if l.get("last_contact")]
        latest_month=max(contact_dates)[:7] if contact_dates else None
        deals_closed_this_month=sum(1 for l in closed if (l.get("last_contact") or "")[:7]==latest_month)
    else: hot,warm,cold=38,89,120

    ragas_path=Path("data/evaluation/ragas_results.json")
    ragas_faithfulness=hallucination_rate=None
    ragas_evaluated=False
    if ragas_path.exists():
        with open(ragas_path) as f: ragas_summary=json.load(f).get("summary",{})
        # a mean computed from too few surviving (non-timed-out) judge calls
        # isn't a real measurement - keep the dashboard honest about that
        if not ragas_summary.get("insufficient_sample", False):
            ragas_faithfulness=ragas_summary.get("faithfulness"); hallucination_rate=ragas_summary.get("hallucination_rate")
            ragas_evaluated=ragas_faithfulness is not None

    avg_latency_ms=round(sum(_request_latencies_ms)/len(_request_latencies_ms),1) if _request_latencies_ms else None

    return {"total_leads":hot+warm+cold,"hot_leads":hot,"warm_leads":warm,"cold_leads":cold,
            "total_properties":len(DEMO_PROPERTIES),"available_properties":len(DEMO_PROPERTIES),
            "ragas_faithfulness":ragas_faithfulness,"hallucination_rate":hallucination_rate,"ragas_evaluated":ragas_evaluated,
            "avg_latency_ms":avg_latency_ms,"requests_this_session":_request_count,
            "session_started_at":_server_start_time,
            "lead_conversion_rate":lead_conversion_rate,"avg_lead_score":avg_lead_score,
            "revenue_pipeline_aed":revenue_pipeline_aed,"deals_closed_this_month":deals_closed_this_month}

import os

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080))
    )

# ── NEW: Valuation endpoint ────────────────────────────────────────────────────
class ValuationReq(BaseModel):
    property_type: str; location: str; bedrooms: int = 0; area_sqft: float = 0
    floor: int = 0; view: str = ""; condition: str = "good"
    furnished: bool = False; asking_price_aed: float = 0

@app.post("/api/tools/valuate", tags=["Tools"])
async def valuate_property(req: ValuationReq):
    from src.agents.valuation_agent import ValuationAgent, ValuationRequest
    return ValuationAgent().estimate(ValuationRequest(**req.model_dump()))

# ── NEW: Mortgage calculator ───────────────────────────────────────────────────
class MortgageReq(BaseModel):
    property_price_aed: float; monthly_income_aed: float = 0
    existing_debts_aed: float = 0; down_payment_pct: float = 25.0
    interest_rate_pct: float = 4.5; tenure_years: int = 25
    is_uae_national: bool = False; is_resident: bool = True

@app.post("/api/tools/mortgage", tags=["Tools"])
async def calc_mortgage(req: MortgageReq):
    from src.agents.mortgage_agent import MortgageAgent, MortgageRequest
    return MortgageAgent().calculate(MortgageRequest(**req.model_dump()))

# ── NEW: Property comparison ───────────────────────────────────────────────────
class CompareReq(BaseModel):
    property_ids: list[str]; buyer_profile: str = ""

@app.post("/api/tools/compare", tags=["Tools"])
async def compare_props(req: CompareReq):
    from src.agents.comparison_agent import ComparisonAgent
    return ComparisonAgent().compare(req.property_ids, req.buyer_profile)

# ── NEW: Force rebuild RAG index ───────────────────────────────────────────────
@app.post("/api/rag/rebuild", tags=["RAG"], dependencies=[Depends(require_admin_key)])
async def rebuild_rag():
    if not _rag: raise HTTPException(503, "RAG not ready")
    n = _rag.rebuild_from_all_docs()
    return {"status": "rebuilt", "documents": n, "chunks": len(_rag._docs)}

# ── NEW: Lead statistics ───────────────────────────────────────────────────────
@app.get("/api/leads/stats", tags=["Lead Scoring"])
async def lead_stats():
    import json
    from pathlib import Path
    p = Path("data/synthetic/leads_200.json")
    if not p.exists(): return {"error": "Not found"}
    leads = json.loads(p.read_text())
    tiers = {}
    sources = {}
    for l in leads:
        t = l.get("tier","COLD"); tiers[t] = tiers.get(t,0)+1
        s = l.get("source","unknown"); sources[s] = sources.get(s,0)+1
    return {"total":len(leads),"tiers":tiers,"sources":sources,
            "avg_score":round(sum(l.get("lead_score",0) for l in leads)/len(leads),1)}
