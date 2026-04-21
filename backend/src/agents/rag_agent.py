import json
from langchain.tools import BaseTool
from pydantic import Field
from src.rag.pipeline import RAGPipeline

class RAGTool(BaseTool):
    name: str = "rag_knowledge_base_tool"
    description: str = "Answers questions about Dubai real estate: DLD fees, mortgages, RERA, Golden Visa, freehold areas, service charges, NOC, rental laws, buying process. Input: plain English question."
    pipeline: RAGPipeline = Field(default_factory=RAGPipeline)
    class Config: arbitrary_types_allowed = True
    def _run(self, q: str) -> str:
        try: return json.dumps(self.pipeline.query(q), indent=2, default=str)
        except Exception as e: return json.dumps({"error":str(e)})
    async def _arun(self, q: str) -> str: return self._run(q)
