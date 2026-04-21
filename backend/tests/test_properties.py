import sys; sys.path.insert(0,'.')
from src.agents.property_retrieval_agent import PropertyRetrievalAgent,PropertyQuery,DEMO_PROPERTIES

def test_all(): a=PropertyRetrievalAgent(); r=a.retrieve(PropertyQuery()); assert len(r["properties"])>0
def test_budget(hot=None): a=PropertyRetrievalAgent(); r=a.retrieve(PropertyQuery(budget_max=1_000_000)); assert all(p["price"]<=1_000_000 for p in r["properties"])
def test_beds(): a=PropertyRetrievalAgent(); r=a.retrieve(PropertyQuery(bedrooms=2)); assert all(p["bedrooms"]==2 for p in r["properties"])
def test_location(): a=PropertyRetrievalAgent(); r=a.retrieve(PropertyQuery(location="Dubai Marina")); assert all("marina" in p["location"].lower() for p in r["properties"])
def test_match_score(): a=PropertyRetrievalAgent(); r=a.retrieve(PropertyQuery(bedrooms=3)); assert all(0<=p["match_score"]<=1 for p in r["properties"])
def test_demo_count(): assert len(DEMO_PROPERTIES)==10
