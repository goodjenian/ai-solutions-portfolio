import langchain.agents as lc_agents
from langchain.memory import ConversationBufferMemory

import agents.hybrid_agent as hybrid_agent


def test_tool_agent_falls_back_when_openai_tools_agent_fails(monkeypatch):
    monkeypatch.setattr(
        hybrid_agent,
        "create_openai_tools_agent",
        lambda **_: (_ for _ in ()).throw(RuntimeError("no tool calling")),
    )

    monkeypatch.setattr(lc_agents, "initialize_agent", lambda **_: "fallback_executor")

    inst = hybrid_agent.HybridPropertyAgent.__new__(hybrid_agent.HybridPropertyAgent)
    inst.llm = object()
    inst.tools = []
    inst.memory = ConversationBufferMemory(
        memory_key="chat_history", return_messages=True, output_key="answer"
    )
    inst.verbose = False

    assert inst._create_tool_agent() == "fallback_executor"
