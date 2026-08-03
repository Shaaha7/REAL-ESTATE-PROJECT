import json
import sys; sys.path.insert(0, '.')
import pytest
from langchain.memory import ConversationBufferWindowMemory

from src.agents.orchestrator import OrchestratorAgent
from src.utils.settings import get_settings

no_llm = not bool(get_settings().active_api_key)
needs_llm = pytest.mark.skipif(no_llm, reason="No GOOGLE_API_KEY/GROQ_API_KEY configured - live orchestrator run needs an LLM")


@pytest.fixture
def orch(tmp_path):
    o = OrchestratorAgent()
    o._storage_dir = tmp_path  # don't touch the real data/conversations dir
    return o


def test_session_path_sanitizes_ids(orch):
    assert orch._session_path("../../etc/passwd").name == "etcpasswd.json"
    assert orch._session_path("session-1699999999").name == "session-1699999999.json"
    assert orch._session_path("").name == "default.json"


def test_save_and_load_round_trip(orch):
    orch._save_turn("s1", "hello", "hi there")
    orch._save_turn("s1", "what properties do you have", "here are some listings")

    mem = ConversationBufferWindowMemory(memory_key="chat_history", return_messages=True, k=10)
    orch._load_history("s1", mem)

    texts = [m.content for m in mem.chat_memory.messages]
    assert texts == ["hello", "hi there", "what properties do you have", "here are some listings"]


def test_sessions_are_isolated_on_disk(orch):
    orch._save_turn("session-a", "message from a", "reply to a")
    orch._save_turn("session-b", "message from b", "reply to b")

    mem_a = ConversationBufferWindowMemory(memory_key="chat_history", return_messages=True, k=10)
    orch._load_history("session-a", mem_a)
    mem_b = ConversationBufferWindowMemory(memory_key="chat_history", return_messages=True, k=10)
    orch._load_history("session-b", mem_b)

    assert [m.content for m in mem_a.chat_memory.messages] == ["message from a", "reply to a"]
    assert [m.content for m in mem_b.chat_memory.messages] == ["message from b", "reply to b"]


def test_history_survives_a_new_agent_instance(orch, tmp_path):
    orch._save_turn("persistent-session", "remember this", "I will remember")

    fresh = OrchestratorAgent()
    fresh._storage_dir = tmp_path
    mem = ConversationBufferWindowMemory(memory_key="chat_history", return_messages=True, k=10)
    fresh._load_history("persistent-session", mem)

    assert [m.content for m in mem.chat_memory.messages] == ["remember this", "I will remember"]


def test_turn_history_is_capped(orch):
    for i in range(60):
        orch._save_turn("busy-session", f"msg {i}", f"reply {i}")
    data = json.loads(orch._session_path("busy-session").read_text())
    assert len(data["turns"]) == 50
    assert data["turns"][-1]["input"] == "msg 59"


def test_get_executor_returns_none_without_llm(orch, monkeypatch):
    monkeypatch.setattr(OrchestratorAgent, "agent", property(lambda self: None))
    assert orch._get_executor("any-session") is None


@needs_llm
def test_two_sessions_do_not_share_memory():
    """Regression test: two different session_ids used to share one global
    ConversationBufferWindowMemory on the OrchestratorAgent singleton, so one
    user's chat history leaked into another user's context."""
    orch = OrchestratorAgent()
    orch.run("My name is Alice and my budget is 2 million AED", session_id="alice-session")
    orch.run("My name is Bob", session_id="bob-session")

    exec_alice = orch._get_executor("alice-session")
    exec_bob = orch._get_executor("bob-session")
    assert exec_alice is not exec_bob
    alice_texts = " ".join(m.content for m in exec_alice.memory.chat_memory.messages)
    bob_texts = " ".join(m.content for m in exec_bob.memory.chat_memory.messages)
    assert "Alice" in alice_texts
    assert "Alice" not in bob_texts
