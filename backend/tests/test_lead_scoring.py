import sys; sys.path.insert(0,'.')
import pytest
from src.agents.lead_scoring_agent import LeadData,LeadScoringAgent,train_lead_scorer

@pytest.fixture
def hot(): return LeadData(lead_id="L001",client_name="Ahmed",budget_aed=2_500_000,property_type="villa",location_preference="Dubai Hills",bedrooms=3,timeline_months=1,num_interactions=8,avg_response_hours=0.5,message_quality_score=0.9,source="referral")
@pytest.fixture
def cold(): return LeadData(lead_id="L002",client_name="X",budget_aed=50_000,timeline_months=24,num_interactions=0,avg_response_hours=72,message_quality_score=0.1,source="web")

def test_model_trains(): assert train_lead_scorer() is not None
def test_score_range(hot): a=LeadScoringAgent(); r=a.score(hot); assert 0<=r.score<=100; assert r.tier in("HOT","WARM","COLD")
def test_hot_beats_cold(hot,cold): a=LeadScoringAgent(); assert a.score(hot).score>a.score(cold).score
def test_shap_list(hot): a=LeadScoringAgent(); r=a.score(hot); assert isinstance(r.shap_top_features,list)
def test_recommended_action(hot): a=LeadScoringAgent(); r=a.score(hot); assert len(r.recommended_action)>10
