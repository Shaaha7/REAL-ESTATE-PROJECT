from __future__ import annotations
import json
from typing import Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from loguru import logger
from src.database.mysql_client import MySQLClient
from src.database.mongo_client import MongoClient

DEMO_PROPERTIES = [
    {"id":"P001","title":"Luxury 3BR Villa — Private Pool & Golf View","location":"Dubai Hills Estate","price":2_150_000,"bedrooms":3,"bathrooms":3.5,"area_sqft":3400,"property_type":"villa","amenities":["private pool","landscaped garden","maids room","2 covered parking","golf view","smart home","BBQ area","24hr security"],"status":"available","images":["https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=800"],"description":"Stunning 3BR villa in prestigious Dubai Hills Estate with private pool, golf views, and premium finishes throughout.","yield_pct":7.0,"service_charge_yearly":27200,"agent":"Ahmed Al Rashidi","rera_no":"12345"},
    {"id":"P002","title":"Modern 2BR Apartment — Full Sea View","location":"Dubai Marina","price":1_350_000,"bedrooms":2,"bathrooms":2.0,"area_sqft":1250,"property_type":"apartment","amenities":["full sea view","infinity rooftop pool","state-of-art gym","concierge 24/7","1 parking","metro 2min walk","chiller free","sauna"],"status":"available","images":["https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800"],"description":"High-floor 2BR with unobstructed sea and marina views. Chiller-free building — save AED 15,000+ per year.","yield_pct":7.4,"service_charge_yearly":17500,"agent":"Sarah Johnson","rera_no":"12346"},
    {"id":"P003","title":"Spacious 1BR — Lake View, Metro Access","location":"Jumeirah Lake Towers","price":680_000,"bedrooms":1,"bathrooms":1.0,"area_sqft":780,"property_type":"apartment","amenities":["lake view","fully equipped gym","covered parking","metro station 1min","JLT dining at doorstep","24hr security"],"status":"available","images":["https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800"],"description":"High-yield 1BR investment in JLT with direct metro access. Consistently rented, low vacancy.","yield_pct":8.2,"service_charge_yearly":10920,"agent":"Mohammed Al Rashidi","rera_no":"12347"},
    {"id":"P004","title":"4BR Family Townhouse — Private Garden","location":"Arabian Ranches","price":3_200_000,"bedrooms":4,"bathrooms":4.0,"area_sqft":4200,"property_type":"townhouse","amenities":["private garden","community pool","kids pool","tennis courts","school within community","2 parking","BBQ area","community park"],"status":"available","images":["https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800"],"description":"Spacious 4BR corner townhouse in Arabian Ranches. One of Dubai's most sought-after family communities.","yield_pct":5.5,"service_charge_yearly":22400,"agent":"Priya Sharma","rera_no":"12348"},
    {"id":"P005","title":"Premium Studio — Burj Khalifa & Fountain View","location":"Downtown Dubai","price":920_000,"bedrooms":0,"bathrooms":1.0,"area_sqft":620,"property_type":"studio","amenities":["Burj Khalifa view","Dubai Fountain view","hotel-style pool","world-class gym","24hr concierge","valet parking","walking distance to Dubai Mall"],"status":"available","images":["https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800"],"description":"Iconic studio with direct views of Burj Khalifa and Dubai Fountain. Perfect as holiday home or investment.","yield_pct":6.2,"service_charge_yearly":13640,"agent":"David Chen","rera_no":"12349"},
    {"id":"P006","title":"3BR Apartment — Dubai Canal & Marina View","location":"Business Bay","price":1_850_000,"bedrooms":3,"bathrooms":2.5,"area_sqft":1900,"property_type":"apartment","amenities":["canal view","gym & pool","2 parking","maid room","metro nearby","walking to DIFC","modern kitchen","storage room"],"status":"available","images":["https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=800"],"description":"Spacious 3BR in Business Bay with stunning canal views. Walk to DIFC, ideal for corporate tenants.","yield_pct":6.8,"service_charge_yearly":28500,"agent":"Fatima Al Zaabi","rera_no":"12350"},
    {"id":"P007","title":"5BR Signature Villa — Private Beach & Infinity Pool","location":"Palm Jumeirah","price":8_500_000,"bedrooms":5,"bathrooms":6.0,"area_sqft":7200,"property_type":"villa","amenities":["25m private beach","infinity pool & jacuzzi","home cinema","Crestron smart home","private boat dock","elevator","outdoor kitchen","staff quarters","5 parking","tropical garden"],"status":"available","images":["https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800"],"description":"Ultra-luxury 5BR frond villa on Palm Jumeirah with 25m private beach, signature pool, and smart home technology.","yield_pct":7.5,"service_charge_yearly":158400,"agent":"Omar Al Maktoum","rera_no":"12351"},
    {"id":"P008","title":"2BR Townhouse — Quiet Family Community","location":"Mirdif","price":1_100_000,"bedrooms":2,"bathrooms":2.0,"area_sqft":1650,"property_type":"townhouse","amenities":["private garden","2 parking","community park","near top schools","quiet neighbourhood","storage room","pets allowed"],"status":"available","images":["https://images.unsplash.com/photo-1484154218962-a197022b5858?w=800"],"description":"Charming 2BR townhouse in family-friendly Mirdif. Near top schools, perfect for families or buy-to-let.","yield_pct":6.1,"service_charge_yearly":8580,"agent":"Emma Thompson","rera_no":"12352"},
    {"id":"P009","title":"3BR Penthouse — 360° Marina Skyline Views","location":"Dubai Marina","price":4_200_000,"bedrooms":3,"bathrooms":3.5,"area_sqft":2800,"property_type":"penthouse","amenities":["360-degree views","3 private terraces","infinity pool access","private gym","valet parking","premium concierge","maid room","private elevator"],"status":"available","images":["https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800"],"description":"Exceptional 3BR penthouse crowning a Dubai Marina tower. Three terraces, 360° panoramic views, private gym.","yield_pct":6.5,"service_charge_yearly":56000,"agent":"Khalid Al Marzouqi","rera_no":"12353"},
    {"id":"P010","title":"1BR High-Yield Investment Apartment","location":"Jumeirah Village Circle","price":550_000,"bedrooms":1,"bathrooms":1.0,"area_sqft":720,"property_type":"apartment","amenities":["pool","fully equipped gym","1 parking","community park","near Circle Mall","pet-friendly","high rental yield","tenanted"],"status":"available","images":["https://images.unsplash.com/photo-1515263487990-61b07816b324?w=800"],"description":"Top-performing 1BR investment in JVC delivering 8%+ gross yield. Currently tenanted at AED 52,000/year.","yield_pct":8.5,"service_charge_yearly":7920,"agent":"Anya Patel","rera_no":"12354"},
]

class PropertyQuery(BaseModel):
    property_type: Optional[str] = None; location: Optional[str] = None
    budget_min: Optional[float] = None; budget_max: Optional[float] = None
    bedrooms: Optional[int] = None; free_text: str = ""

class PropertyRetrievalAgent:
    def __init__(self):
        self._mysql = MySQLClient()
        self._mongo = MongoClient()

    def _filter(self, q: PropertyQuery) -> list[dict]:
        r = list(DEMO_PROPERTIES)
        if q.budget_max: r = [p for p in r if p["price"] <= q.budget_max]
        if q.budget_min: r = [p for p in r if p["price"] >= q.budget_min]
        if q.bedrooms is not None: r = [p for p in r if p["bedrooms"] == q.bedrooms]
        if q.location: r = [p for p in r if q.location.lower() in p["location"].lower()]
        if q.property_type: r = [p for p in r if q.property_type.lower() in p["property_type"].lower()]
        return r

    def _mysql_search(self, q: PropertyQuery) -> Optional[list[dict]]:
        """Structured filter search. Returns None only if MySQL is unreachable -
        an empty list is a real (if unsatisfying) answer and must not fall back."""
        if self._mysql.engine is None: return None
        sql, params = "SELECT * FROM properties WHERE 1=1", {}
        if q.budget_max is not None: sql += " AND price <= :budget_max"; params["budget_max"] = q.budget_max
        if q.budget_min is not None: sql += " AND price >= :budget_min"; params["budget_min"] = q.budget_min
        if q.bedrooms is not None: sql += " AND bedrooms = :bedrooms"; params["bedrooms"] = q.bedrooms
        if q.location: sql += " AND LOWER(location) LIKE :location"; params["location"] = f"%{q.location.lower()}%"
        if q.property_type: sql += " AND LOWER(property_type) LIKE :property_type"; params["property_type"] = f"%{q.property_type.lower()}%"
        try:
            rows = self._mysql.execute_query(sql, params)
        except Exception as e:
            logger.warning(f"MySQL property search failed, falling back: {e}")
            return None
        for r in rows:
            for field in ("amenities", "images"):
                if isinstance(r.get(field), str):
                    try: r[field] = json.loads(r[field])
                    except Exception: r[field] = []
        return rows

    def _mongo_search(self, q: PropertyQuery) -> Optional[list[dict]]:
        """Free-text search over description/amenities/title/location. None only if
        MongoDB is unreachable; an empty list is a legitimate no-match result."""
        if self._mongo.db is None: return None
        try:
            filter_doc = {"$text": {"$search": q.free_text}} if q.free_text else {}
            return self._mongo.find("properties", filter_doc, limit=20)
        except Exception as e:
            logger.warning(f"MongoDB property search failed, falling back: {e}")
            return None

    def _score(self, p: dict, q: PropertyQuery) -> tuple[float, list[str]]:
        criteria = [q.location, q.budget_max, q.bedrooms, q.property_type]
        total = sum(1 for c in criteria if c not in (None, ""))
        matched, reasons = 0, []
        if q.location and q.location.lower() in p["location"].lower():
            matched += 1; reasons.append(f"Located in {p['location']}")
        if q.budget_max and p["price"] <= q.budget_max:
            matched += 1; reasons.append(f"Within AED {q.budget_max:,.0f} budget")
        if q.bedrooms is not None and p["bedrooms"] == q.bedrooms:
            matched += 1; reasons.append(f"Exactly {q.bedrooms}BR as requested")
        if q.property_type and q.property_type.lower() in p["property_type"].lower():
            matched += 1; reasons.append(f"Matches requested {q.property_type} type")
        if not reasons: reasons.append("Matches your search criteria")
        score = 0.6 + 0.4 * (matched / total) if total else 0.75
        return round(score, 3), reasons

    def retrieve(self, q: PropertyQuery) -> dict:
        want_structured = bool(q.property_type or q.location or q.budget_min or q.budget_max or q.bedrooms is not None) or not q.free_text
        want_text = bool(q.free_text)

        mysql_results = self._mysql_search(q) if want_structured else None
        mongo_results = self._mongo_search(q) if want_text else None

        if mysql_results is not None and mongo_results is not None:
            merged = {p["id"]: p for p in mysql_results}
            for p in mongo_results: merged.setdefault(p["id"], p)
            candidates, route = list(merged.values()), "mysql+mongodb"
        elif mysql_results is not None:
            candidates, route = mysql_results, "mysql"
        elif mongo_results is not None:
            candidates, route = mongo_results, "mongodb"
        else:
            candidates, route = self._filter(q) or list(DEMO_PROPERTIES[:5]), "demo_fallback"

        source = "demo_data" if route == "demo_fallback" else route
        results = []
        for p in candidates[:5]:
            score, reasons = self._score(p, q)
            results.append({**p, "match_score": score, "match_reasons": reasons, "source": source})
        results.sort(key=lambda x: x["match_score"], reverse=True)
        return {"query":q.model_dump(),"source_routed":route,"properties":results,"total_candidates":len(candidates),"returned":len(results)}

class PropertyRetrievalTool(BaseTool):
    name: str = "property_retrieval_tool"
    description: str = "Searches real estate properties. Input JSON: property_type,location,budget_min,budget_max,bedrooms,free_text."
    agent: PropertyRetrievalAgent = Field(default_factory=PropertyRetrievalAgent)
    class Config: arbitrary_types_allowed = True
    def _run(self, s: str) -> str:
        try:
            data = json.loads(s) if isinstance(s,str) else s
            return json.dumps(self.agent.retrieve(PropertyQuery(**data)), indent=2, default=str)
        except Exception as e: return json.dumps({"error":str(e)})
    async def _arun(self, s: str) -> str: return self._run(s)
