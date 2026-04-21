from __future__ import annotations
import json, time
from typing import Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from loguru import logger
from src.utils.settings import get_settings

class LLMClient:
    def __init__(self):
        self.settings = get_settings()
        self._primary: Optional[BaseChatModel] = None

    @property
    def langchain_llm(self) -> Optional[BaseChatModel]:
        if self._primary is None:
            try:
                s = self.settings
                if s.llm_provider == "groq" and s.groq_api_key:
                    from langchain_groq import ChatGroq
                    self._primary = ChatGroq(model=s.groq_model, api_key=s.groq_api_key,
                        temperature=s.llm_temperature, max_tokens=s.llm_max_tokens, timeout=s.llm_timeout, max_retries=3)
                    logger.info(f"LLM: Groq {s.groq_model} (free)")
                elif s.google_api_key:
                    from langchain_google_genai import ChatGoogleGenerativeAI
                    self._primary = ChatGoogleGenerativeAI(model=s.gemini_model, google_api_key=s.google_api_key,
                        temperature=s.llm_temperature, max_output_tokens=s.llm_max_tokens, timeout=s.llm_timeout, max_retries=3)
                    logger.info(f"LLM: Gemini {s.gemini_model} (free)")
                else:
                    logger.warning("No LLM key. Add GOOGLE_API_KEY or GROQ_API_KEY to .env")
            except Exception as e:
                logger.error(f"LLM init failed: {e}")
        return self._primary

    def invoke(self, system_prompt: str, user_message: str, expect_json: bool = True) -> dict | str:
        if not self.langchain_llm:
            return {"error":"No LLM configured","response":"Add API key to .env file","confidence":0.0}
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
        for attempt in range(3):
            try:
                t0 = time.perf_counter()
                resp = self.langchain_llm.invoke(messages)
                logger.debug(f"LLM {round((time.perf_counter()-t0)*1000)}ms attempt {attempt+1}")
                return self._parse_json(resp.content) if expect_json else resp.content
            except Exception as e:
                if attempt < 2: time.sleep(2 ** attempt)
                else: logger.error(f"LLM failed: {e}")
        return {"error":"LLM failed after retries","confidence":0.0}

    def _parse_json(self, raw: str) -> dict:
        c = raw.strip()
        if c.startswith("```"):
            c = "\n".join(l for l in c.split("\n") if not l.strip().startswith("```")).strip()
        try:
            return json.loads(c)
        except Exception:
            s, e = c.find("{"), c.rfind("}")+1
            if s != -1 and e > s:
                try: return json.loads(c[s:e])
                except: pass
        return {"raw_response": raw, "parse_error": True}
