from __future__ import annotations
import json, re, time
from pathlib import Path
from typing import Optional
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from loguru import logger
from src.utils.settings import get_settings
from src.utils.llm_client import LLMClient
from src.prompts.templates import ORCHESTRATOR_SYSTEM
# torch (via RAGTool's RAGPipeline) must import before xgboost (via
# LeadScoringTool) - see the matching comment in app.py.
from src.agents.rag_agent import RAGTool
from src.agents.lead_scoring_agent import LeadScoringTool
from src.agents.property_retrieval_agent import PropertyRetrievalTool
from src.agents.communication_agent import CommunicationTool
from src.agents.explainability_agent import ExplainabilityTool

class OrchestratorAgent:
    # cap how many distinct sessions stay warm in memory at once - each
    # session_id is client-supplied, so an unbounded dict is a memory leak
    MAX_CACHED_SESSIONS = 200
    HISTORY_WINDOW = 10

    def __init__(self):
        self.settings = get_settings(); self.llm_client = LLMClient()
        self._agent = None
        self._executors: dict[str, AgentExecutor] = {}
        self.tools = [LeadScoringTool(), PropertyRetrievalTool(), RAGTool(), CommunicationTool(), ExplainabilityTool()]
        self._storage_dir = Path("data/conversations")
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    @property
    def agent(self):
        if self._agent is None:
            llm = self.llm_client.langchain_llm
            if llm is None: return None
            try:
                prompt = ChatPromptTemplate.from_messages([("system",ORCHESTRATOR_SYSTEM),MessagesPlaceholder("chat_history"),("human","{input}"),MessagesPlaceholder("agent_scratchpad")])
                self._agent = create_tool_calling_agent(llm, self.tools, prompt)
                logger.success("Orchestrator agent ready")
            except Exception as e: logger.error(f"Agent build failed: {e}")
        return self._agent

    def _session_path(self, session_id: str) -> Path:
        safe_id = re.sub(r'[^a-zA-Z0-9_-]', '', session_id)[:100] or "default"
        return self._storage_dir / f"{safe_id}.json"

    def _load_history(self, session_id: str, memory: ConversationBufferWindowMemory) -> None:
        p = self._session_path(session_id)
        if not p.exists(): return
        try:
            turns = json.loads(p.read_text()).get("turns", [])[-self.HISTORY_WINDOW:]
            for turn in turns:
                memory.chat_memory.add_user_message(turn["input"])
                memory.chat_memory.add_ai_message(turn["output"])
        except Exception as e:
            logger.warning(f"Failed to load conversation history for session {session_id}: {e}")

    def _save_turn(self, session_id: str, user_input: str, output_text: str) -> None:
        p = self._session_path(session_id)
        data = {"turns": []}
        if p.exists():
            try: data = json.loads(p.read_text())
            except Exception: pass
        data.setdefault("turns", []).append({"input": user_input, "output": output_text, "ts": time.time()})
        data["turns"] = data["turns"][-50:]
        try: p.write_text(json.dumps(data, default=str))
        except Exception as e: logger.warning(f"Failed to persist conversation turn for session {session_id}: {e}")

    def _get_executor(self, session_id: str) -> Optional[AgentExecutor]:
        if session_id in self._executors:
            return self._executors[session_id]
        agent = self.agent
        if agent is None: return None
        memory = ConversationBufferWindowMemory(memory_key="chat_history", return_messages=True, k=self.HISTORY_WINDOW)
        self._load_history(session_id, memory)
        executor = AgentExecutor(agent=agent,tools=self.tools,memory=memory,verbose=False,max_iterations=8,handle_parsing_errors=True,return_intermediate_steps=True)
        if len(self._executors) >= self.MAX_CACHED_SESSIONS:
            self._executors.pop(next(iter(self._executors)))  # evict oldest
        self._executors[session_id] = executor
        return executor

    def _redact(self, t: str) -> str:
        t = re.sub(r'\+?\d[\d\s\-]{8,}\d','[PHONE]',t)
        return re.sub(r'\b[\w.+-]+@[\w-]+\.\w+\b','[EMAIL]',t)

    def run(self, user_input: str, session_id: str = "default") -> dict:
        t0 = time.perf_counter()
        logger.info(f"[{session_id}] Input: {self._redact(user_input)[:100]}")
        steps = []; output = None
        executor = self._get_executor(session_id)
        if executor:
            try:
                raw = executor.invoke({"input":user_input,"chat_history":executor.memory.chat_memory.messages})
                output = raw.get("output", raw)
                steps = [{"tool":s[0].tool,"tool_input":str(s[0].tool_input)[:200],"observation":str(s[1])[:200]} for s in raw.get("intermediate_steps",[])]
            except Exception as e:
                logger.warning(f"Executor failed ({e}), falling back to direct LLM")
        if output is None:
            try: output = self.llm_client.invoke(ORCHESTRATOR_SYSTEM, user_input, expect_json=True)
            except Exception as e: output = {"response":f"Error: {e}","confidence":0.0,"requires_human_review":True}
        if isinstance(output,dict) and float(output.get("confidence",1.0))<0.70:
            output["requires_human_review"] = True
        output_text = output.get("response", str(output)) if isinstance(output, dict) else str(output)
        self._save_turn(session_id, user_input, output_text)
        return {"session_id":session_id,"input":user_input,"output":output,"intermediate_steps":steps,"latency_ms":round((time.perf_counter()-t0)*1000,2),"provider":self.settings.llm_provider}
