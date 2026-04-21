from __future__ import annotations
import json, re, time
from typing import Optional
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from loguru import logger
from src.utils.settings import get_settings
from src.utils.llm_client import LLMClient
from src.prompts.templates import ORCHESTRATOR_SYSTEM
from src.agents.lead_scoring_agent import LeadScoringTool
from src.agents.property_retrieval_agent import PropertyRetrievalTool
from src.agents.rag_agent import RAGTool
from src.agents.communication_agent import CommunicationTool
from src.agents.explainability_agent import ExplainabilityTool

class OrchestratorAgent:
    def __init__(self):
        self.settings = get_settings(); self.llm_client = LLMClient()
        self._executor: Optional[AgentExecutor] = None
        self.memory = ConversationBufferWindowMemory(memory_key="chat_history", return_messages=True, k=10)
        self.tools = [LeadScoringTool(), PropertyRetrievalTool(), RAGTool(), CommunicationTool(), ExplainabilityTool()]

    @property
    def executor(self) -> Optional[AgentExecutor]:
        if self._executor is None:
            llm = self.llm_client.langchain_llm
            if llm is None: return None
            try:
                prompt = ChatPromptTemplate.from_messages([("system",ORCHESTRATOR_SYSTEM),MessagesPlaceholder("chat_history"),("human","{input}"),MessagesPlaceholder("agent_scratchpad")])
                agent = create_tool_calling_agent(llm, self.tools, prompt)
                self._executor = AgentExecutor(agent=agent,tools=self.tools,memory=self.memory,verbose=False,max_iterations=8,handle_parsing_errors=True,return_intermediate_steps=True)
                logger.success("Orchestrator agent executor ready")
            except Exception as e: logger.error(f"Executor failed: {e}")
        return self._executor

    def _redact(self, t: str) -> str:
        t = re.sub(r'\+?\d[\d\s\-]{8,}\d','[PHONE]',t)
        return re.sub(r'\b[\w.+-]+@[\w-]+\.\w+\b','[EMAIL]',t)

    def run(self, user_input: str, session_id: str = "default") -> dict:
        t0 = time.perf_counter()
        logger.info(f"[{session_id}] Input: {self._redact(user_input)[:100]}")
        steps = []; output = None
        if self.executor:
            try:
                raw = self.executor.invoke({"input":user_input,"chat_history":self.memory.chat_memory.messages})
                output = raw.get("output", raw)
                steps = [{"tool":s[0].tool,"tool_input":str(s[0].tool_input)[:200],"observation":str(s[1])[:200]} for s in raw.get("intermediate_steps",[])]
            except Exception as e:
                logger.warning(f"Executor failed ({e}), falling back to direct LLM")
        if output is None:
            try: output = self.llm_client.invoke(ORCHESTRATOR_SYSTEM, user_input, expect_json=True)
            except Exception as e: output = {"response":f"Error: {e}","confidence":0.0,"requires_human_review":True}
        if isinstance(output,dict) and float(output.get("confidence",1.0))<0.70:
            output["requires_human_review"] = True
        return {"session_id":session_id,"input":user_input,"output":output,"intermediate_steps":steps,"latency_ms":round((time.perf_counter()-t0)*1000,2),"provider":self.settings.llm_provider}
