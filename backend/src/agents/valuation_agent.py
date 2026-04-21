"""
NEW AGENT: Valuation Agent
Drop into: backend/src/agents/valuation_agent.py
Estimates property market value using comparables and area benchmarks.
"""
from __future__ import annotations
import json
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from loguru import logger
from src.utils.llm_client import LLMClient

VALUATION_SYSTEM = """You are a Dubai property valuation expert with access to DLD transaction data and market benchmarks.

PRICE BENCHMARKS (AED per sqft, 2024):
Studios/1BR:
- International City: 400-600 | JVC: 700-1000 | JLT: 900-1400
- Dubai Marina: 1200-2000 | Downtown: 1500-2800 | Palm Apt: 1800-3500

Villas/Townhouses (AED per sqft BUA):
- JVC villas: 800-1200 | Mirdif: 700-1000 | Arabian Ranches: 1000-1800
- Dubai Hills: 1200-2200 | Palm Fronds: 3000-7000 | Emirates Hills: 4000-9000

VALUATION METHOD:
1. Get price/sqft for area and property type
2. Adjust for: floor level (+2% per 5 floors above ground), view premium (+10-20% for sea/burj/golf)
3. Adjust for: condition (new=0%, good=-5%, needs work=-10-15%)
4. Adjust for: furnished (+10-15% for quality furnishing)
5. Cross-check against recent transactions

Respond ONLY in JSON:
{
  "estimated_value_aed": <number>,
  "value_range_low_aed": <number>,
  "value_range_high_aed": <number>,
  "price_per_sqft": <number>,
  "method": "<explanation of valuation method>",
  "comparable_areas": ["<area>: AED X/sqft"],
  "value_drivers": ["<positive factor>"],
  "value_detractors": ["<negative factor>"],
  "confidence": <0.0-1.0>,
  "recommendation": "<buy/fair/overpriced and why>"
}"""

class ValuationRequest(BaseModel):
    property_type: str  # apartment, villa, townhouse, penthouse, studio
    location: str       # area in Dubai
    bedrooms: int = 0
    area_sqft: float = 0
    floor: int = 0
    view: str = ""        # sea, burj, golf, community, street
    condition: str = "good"  # new, good, needs_work
    furnished: bool = False
    asking_price_aed: float = 0  # optional — to check if fair

class ValuationAgent:
    def __init__(self):
        self.llm = LLMClient()

    def estimate(self, req: ValuationRequest) -> dict:
        logger.info(f"Valuation: {req.bedrooms}BR {req.property_type} in {req.location} ({req.area_sqft}sqft)")
        prompt = f"""Estimate market value for:
- Type: {req.bedrooms}BR {req.property_type}
- Location: {req.location}, Dubai
- Size: {req.area_sqft} sqft
- Floor: {req.floor if req.floor else 'not specified'}
- View: {req.view if req.view else 'standard community view'}
- Condition: {req.condition}
- Furnished: {'Yes' if req.furnished else 'No'}
- Asking price (if any): {'AED ' + f'{req.asking_price_aed:,.0f}' if req.asking_price_aed else 'Not specified'}

Provide detailed valuation with method explanation."""
        return self.llm.invoke(VALUATION_SYSTEM, prompt, expect_json=True)

class ValuationTool(BaseTool):
    name: str = "property_valuation_tool"
    description: str = (
        "Estimates Dubai property market value. "
        "Input JSON: property_type, location, bedrooms, area_sqft, floor, view, condition, furnished, asking_price_aed. "
        "Output: estimated value, range, price/sqft, recommendation."
    )
    agent: ValuationAgent = Field(default_factory=ValuationAgent)
    class Config: arbitrary_types_allowed = True

    def _run(self, s: str) -> str:
        try:
            data = json.loads(s) if isinstance(s, str) else s
            result = self.agent.estimate(ValuationRequest(**data))
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def _arun(self, s: str) -> str:
        return self._run(s)
