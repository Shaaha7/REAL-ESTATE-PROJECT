from __future__ import annotations
import json, joblib
from pathlib import Path
from typing import Optional
import numpy as np, pandas as pd, shap, mlflow, mlflow.sklearn
from langchain.tools import BaseTool
from loguru import logger
from pydantic import BaseModel, Field
from src.utils.settings import get_settings
from src.utils.llm_client import LLMClient
from src.prompts.templates import LEAD_SCORING_SYSTEM

class LeadData(BaseModel):
    lead_id: str = "lead-001"; client_name: str; budget_aed: float = Field(0.0, ge=0)
    property_type: str = "apartment"; location_preference: str = ""; bedrooms: Optional[int] = None
    timeline_months: Optional[int] = None; num_interactions: int = Field(0, ge=0)
    avg_response_hours: float = Field(24.0, ge=0); message_quality_score: float = Field(0.5, ge=0, le=1)
    source: str = "web"

class LeadScore(BaseModel):
    lead_id: str; client_name: str; score: float; tier: str
    budget_score: float; urgency_score: float; engagement_score: float
    property_match_score: float; communication_score: float
    recommended_action: str; reasoning: str; shap_top_features: list[dict] = []

MODEL_PATH = Path("data/models/lead_scorer.pkl")
TRAINING_DATA_PATH = Path("data/synthetic/lead_training_data_3000.csv")

def train_lead_scorer():
    from xgboost import XGBRegressor
    logger.info("Training XGBoost lead scorer on 3000-record synthetic dataset…")
    if TRAINING_DATA_PATH.exists():
        df = pd.read_csv(TRAINING_DATA_PATH)
        feature_cols = ["budget_normalized","urgency_score","engagement_score","property_match_score","response_time_score","communication_quality_score","location_preference_match"]
        X = df[feature_cols]; y = df["lead_score_target"]
        logger.info(f"Loaded training data: {len(X)} records")
    else:
        logger.warning("Training CSV not found, generating synthetic data…")
        rng = np.random.default_rng(42); n = 3000
        X = pd.DataFrame({"budget_normalized":rng.uniform(0,1,n),"urgency_score":rng.uniform(0,100,n),"engagement_score":rng.uniform(0,100,n),"property_match_score":rng.uniform(0,100,n),"response_time_score":rng.uniform(0,100,n),"communication_quality_score":rng.uniform(0,100,n),"location_preference_match":rng.uniform(0,1,n)})
        y = (X["budget_normalized"]*25+X["urgency_score"]*0.20+X["engagement_score"]*0.20+X["property_match_score"]*0.15+X["response_time_score"]*0.10+X["communication_quality_score"]*0.10+rng.normal(0,5,n)).clip(0,100)
    model = XGBRegressor(n_estimators=200, max_depth=5, learning_rate=0.05, random_state=42, verbosity=0)
    s = get_settings(); mlflow.set_tracking_uri(s.mlflow_tracking_uri); mlflow.set_experiment("realestate-lead-scoring")
    with mlflow.start_run(run_name="xgboost_lead_scorer"):
        model.fit(X, y)
        mlflow.log_params({"n_estimators":200,"max_depth":5,"learning_rate":0.05,"training_samples":len(X)})
        mlflow.sklearn.log_model(model, "lead_scorer")
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    logger.success(f"Lead scorer saved → {MODEL_PATH}"); return model

class LeadScoringAgent:
    def __init__(self):
        self.settings = get_settings(); self.llm = LLMClient()
        self._model = None; self._explainer = None

    @property
    def model(self):
        if self._model is None:
            self._model = joblib.load(MODEL_PATH) if MODEL_PATH.exists() else train_lead_scorer()
        return self._model

    def _build_features(self, lead: LeadData) -> pd.DataFrame:
        return pd.DataFrame([{"budget_normalized":min(lead.budget_aed/20_000_000,1.0),"urgency_score":max(0.0,100-(lead.timeline_months or 12)*8.33),"engagement_score":min(100.0,lead.num_interactions*10),"property_match_score":80.0 if lead.bedrooms else 50.0,"response_time_score":max(0.0,100-(lead.avg_response_hours/24)*10),"communication_quality_score":lead.message_quality_score*100,"location_preference_match":1.0 if lead.location_preference else 0.5}])

    def _shap(self, X: pd.DataFrame) -> list[dict]:
        try:
            if self._explainer is None: self._explainer = shap.TreeExplainer(self.model)
            sv = self._explainer.shap_values(X)[0]
            return sorted([{"feature":c,"shap_value":round(float(v),4),"direction":"increases_score" if v>0 else "decreases_score"} for c,v in zip(X.columns,sv)],key=lambda x:abs(x["shap_value"]),reverse=True)[:5]
        except Exception as e: logger.warning(f"SHAP failed: {e}"); return []

    def score(self, lead: LeadData) -> LeadScore:
        logger.info(f"Scoring lead: {lead.lead_id} | {lead.client_name}")
        X = self._build_features(lead)
        ml_score = float(np.clip(self.model.predict(X)[0],0,100))
        shap_top = self._shap(X)
        llm_score = ml_score; reasoning = f"ML score: {ml_score:.1f}"
        try:
            msg = f"Client: {lead.client_name}\nBudget: AED {lead.budget_aed:,.0f}\nProperty: {lead.bedrooms}BR {lead.property_type}{' in '+lead.location_preference if lead.location_preference else ''}\nTimeline: {lead.timeline_months or 'unspecified'} months\nInteractions: {lead.num_interactions} | Avg response: {lead.avg_response_hours:.1f}h\nMessage quality: {lead.message_quality_score:.1%}\nSource: {lead.source}"
            r = self.llm.invoke(LEAD_SCORING_SYSTEM, msg, expect_json=True)
            if isinstance(r,dict) and "lead_score" in r:
                llm_score = float(r["lead_score"]); reasoning = r.get("reasoning", reasoning)
        except Exception as e: logger.warning(f"LLM scoring failed: {e}")
        final = round(ml_score*0.6+llm_score*0.4,2)
        tier = "HOT" if final>=75 else "WARM" if final>=50 else "COLD"
        actions = {"HOT":"Immediate callback within 2 hours. Send 3 matching properties today.","WARM":"Send curated shortlist within 24h. Follow up in 3 days.","COLD":"Add to monthly nurture campaign. Re-evaluate in 30 days."}
        f = X.iloc[0]
        return LeadScore(lead_id=lead.lead_id,client_name=lead.client_name,score=final,tier=tier,
            budget_score=round(float(f["budget_normalized"])*100,2),urgency_score=round(float(f["urgency_score"]),2),
            engagement_score=round(float(f["engagement_score"]),2),property_match_score=round(float(f["property_match_score"]),2),
            communication_score=round(float(f["communication_quality_score"]),2),
            recommended_action=actions[tier],reasoning=reasoning,shap_top_features=shap_top)

class LeadScoringTool(BaseTool):
    name: str = "lead_scoring_tool"
    description: str = "Scores real estate leads. Input JSON: lead_id,client_name,budget_aed,property_type,location_preference,bedrooms,timeline_months,num_interactions,avg_response_hours,message_quality_score,source."
    agent: LeadScoringAgent = Field(default_factory=LeadScoringAgent)
    class Config: arbitrary_types_allowed = True
    def _run(self, s: str) -> str:
        try:
            data = json.loads(s) if isinstance(s,str) else s
            return self.agent.score(LeadData(**data)).model_dump_json(indent=2)
        except Exception as e: return json.dumps({"error":str(e)})
    async def _arun(self, s: str) -> str: return self._run(s)
