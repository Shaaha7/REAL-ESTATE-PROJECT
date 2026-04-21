import json
from langchain.tools import BaseTool
from pydantic import Field
from src.utils.llm_client import LLMClient
from src.prompts.templates import COMMUNICATION_SYSTEM

class CommunicationTool(BaseTool):
    name: str = "communication_draft_tool"
    description: str = "Drafts professional real estate client emails. Input JSON: lead_score,client_name,interest,timeline,budget."
    llm: LLMClient = Field(default_factory=LLMClient)
    class Config: arbitrary_types_allowed = True
    def _run(self, s: str) -> str:
        try:
            data = json.loads(s) if isinstance(s,str) else s
            return json.dumps(self.llm.invoke(COMMUNICATION_SYSTEM, f"Draft for:\n{json.dumps(data,indent=2)}"), indent=2)
        except Exception as e: return json.dumps({"error":str(e)})
    async def _arun(self, s: str) -> str: return self._run(s)
