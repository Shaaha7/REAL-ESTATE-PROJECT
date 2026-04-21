"""
NEW AGENT: Property Comparison Agent
Drop into: backend/src/agents/comparison_agent.py
Compares 2-3 properties side by side.
"""
from __future__ import annotations
import json
from langchain.tools import BaseTool
from pydantic import Field
from loguru import logger
from src.utils.llm_client import LLMClient
from src.agents.property_retrieval_agent import DEMO_PROPERTIES

COMPARISON_SYSTEM = """You are a Dubai real estate analyst. Compare properties objectively.

Analyse: price, location, size, yield, amenities, pros/cons, who each property suits.

Respond ONLY in JSON:
{
  "winner_overall": "<property_id>",
  "winner_investment": "<property_id>",
  "winner_lifestyle": "<property_id>",
  "comparison_table": [
    {"metric":"Price","values":{"P001":"AED X","P002":"AED Y"}},
    {"metric":"Price/sqft","values":{}},
    {"metric":"Gross Yield","values":{}},
    {"metric":"Location Rating","values":{}},
    {"metric":"Transport","values":{}},
    {"metric":"Schools Nearby","values":{}},
    {"metric":"Best For","values":{}}
  ],
  "property_verdicts": {
    "<id>": {"pros":["<pro>"],"cons":["<con>"],"best_for":"<profile>"}
  },
  "recommendation": "<detailed recommendation based on buyer profile>"
}"""

class ComparisonAgent:
    def __init__(self):
        self.llm = LLMClient()

    def compare(self, property_ids: list[str], buyer_profile: str = "") -> dict:
        props = [p for p in DEMO_PROPERTIES if p["id"] in property_ids]
        if len(props) < 2:
            return {"error": "Need at least 2 valid property IDs to compare"}

        prompt = f"""Compare these {len(props)} Dubai properties:

{json.dumps(props, indent=2, default=str)}

Buyer profile: {buyer_profile if buyer_profile else 'Not specified'}

Provide detailed side-by-side comparison."""
        return self.llm.invoke(COMPARISON_SYSTEM, prompt, expect_json=True)

class ComparisonTool(BaseTool):
    name: str = "property_comparison_tool"
    description: str = (
        "Compares 2-3 Dubai properties side by side. "
        "Input JSON: property_ids (list of P001-P010), buyer_profile (optional string). "
        "Output: comparison table, winner for investment/lifestyle, pros/cons each."
    )
    agent: ComparisonAgent = Field(default_factory=ComparisonAgent)
    class Config: arbitrary_types_allowed = True

    def _run(self, s: str) -> str:
        try:
            data = json.loads(s) if isinstance(s, str) else s
            ids = data.get("property_ids", [])
            profile = data.get("buyer_profile", "")
            return json.dumps(self.agent.compare(ids, profile), indent=2, default=str)
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def _arun(self, s: str) -> str:
        return self._run(s)
