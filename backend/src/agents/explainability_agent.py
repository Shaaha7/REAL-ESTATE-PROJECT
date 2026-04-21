import json
from langchain.tools import BaseTool
from pydantic import Field
from src.utils.llm_client import LLMClient
from src.prompts.templates import EXPLAINABILITY_SYSTEM

class ExplainabilityTool(BaseTool):
    name: str = "explainability_tool"
    description: str = "Generates SHAP attribution reports. Input JSON: decision_type,score,shap_values,context."
    llm: LLMClient = Field(default_factory=LLMClient)
    class Config: arbitrary_types_allowed = True
    def _run(self, s: str) -> str:
        try:
            data = json.loads(s) if isinstance(s,str) else s
            return json.dumps(self.llm.invoke(EXPLAINABILITY_SYSTEM, f"Explain:\n{json.dumps(data,indent=2)}"), indent=2)
        except Exception as e: return json.dumps({"error":str(e)})
    async def _arun(self, s: str) -> str: return self._run(s)
