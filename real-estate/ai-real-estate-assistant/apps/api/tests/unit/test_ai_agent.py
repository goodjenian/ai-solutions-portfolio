import pandas as pd
import pytest


def test_real_estate_gpt_init_requires_optional_langchain_experimental(monkeypatch):
    from ai import agent as agent_module

    monkeypatch.setattr(agent_module, "create_pandas_dataframe_agent", None)

    with pytest.raises(ImportError, match="langchain-experimental"):
        agent_module.RealEstateGPT(pd.DataFrame({"x": [1]}), key="test-key")


def test_real_estate_gpt_optional_import_sets_none_when_missing(monkeypatch):
    import builtins
    import importlib

    from ai import agent as agent_module

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("langchain_experimental"):
            raise ImportError("missing optional dependency")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    importlib.reload(agent_module)
    assert agent_module.create_pandas_dataframe_agent is None

    monkeypatch.setattr(builtins, "__import__", real_import)
    importlib.reload(agent_module)


def test_real_estate_gpt_ask_qn_updates_history_and_uses_prompt(monkeypatch):
    from ai import agent as agent_module

    class DummyLLM:
        def __init__(self, *args, **kwargs):
            self.kwargs = kwargs

    class DummyAgent:
        def __init__(self):
            self.prompts = []

        def run(self, prompt: str) -> str:
            self.prompts.append(prompt)
            return "ok"

    dummy_agent = DummyAgent()

    def fake_create_agent(*args, **kwargs):
        return dummy_agent

    monkeypatch.setattr(agent_module, "ChatOpenAI", DummyLLM)
    monkeypatch.setattr(agent_module, "create_pandas_dataframe_agent", fake_create_agent)

    gpt = agent_module.RealEstateGPT(pd.DataFrame({"x": [1]}), key="test-key")

    answer1 = gpt.ask_qn("What is the cheapest property?")
    assert answer1 == "ok"
    assert len(gpt.conversation_history) == 1
    assert gpt.conversation_history[0]["User"] == "What is the cheapest property?"
    assert gpt.conversation_history[0]["Assistant"] == "ok"

    answer2 = gpt.ask_qn("And with parking?")
    assert answer2 == "ok"
    assert len(gpt.conversation_history) == 2

    assert len(dummy_agent.prompts) == 2
    assert "System: You are a specialized real estate assistant" in dummy_agent.prompts[0]
    assert "User: What is the cheapest property?" in dummy_agent.prompts[0]
    assert (
        "Assistant: Please keep responses relevant to real estate only." in dummy_agent.prompts[0]
    )
    assert "User: What is the cheapest property?" in dummy_agent.prompts[1]
    assert "Assistant: ok" in dummy_agent.prompts[1]
    assert "User: And with parking?" in dummy_agent.prompts[1]


def test_real_estate_gpt_ask_qn_error_returns_message_and_does_not_append(monkeypatch):
    from ai import agent as agent_module

    class DummyLLM:
        def __init__(self, *args, **kwargs):
            self.kwargs = kwargs

    class FailingAgent:
        def run(self, prompt: str) -> str:
            raise ValueError("boom")

    monkeypatch.setattr(agent_module, "ChatOpenAI", DummyLLM)
    monkeypatch.setattr(
        agent_module, "create_pandas_dataframe_agent", lambda *args, **kwargs: FailingAgent()
    )

    gpt = agent_module.RealEstateGPT(pd.DataFrame({"x": [1]}), key="test-key")
    answer = gpt.ask_qn("test question")

    assert answer.startswith("GPT Error:")
    assert "test question" in answer
    assert len(gpt.conversation_history) == 0
