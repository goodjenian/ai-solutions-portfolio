"""Unit tests for HybridPropertyAgent routing logic."""

from unittest.mock import MagicMock, patch

import pytest

from agents.query_analyzer import Complexity, QueryAnalysis, QueryIntent, Tool


class TestQueryAnalysisRouting:
    """Tests for QueryAnalysis routing decision methods."""

    def test_should_use_agent_complex_query(self):
        """Complex queries should use agent."""
        analysis = QueryAnalysis(
            query="Compare prices across all cities and calculate ROI",
            intent=QueryIntent.COMPARISON,
            complexity=Complexity.COMPLEX,
            tools_needed=[Tool.RAG_RETRIEVAL, Tool.COMPARATOR],
        )
        assert analysis.should_use_agent() is True

    def test_should_use_agent_requires_computation(self):
        """Queries requiring computation should use agent."""
        analysis = QueryAnalysis(
            query="Calculate mortgage for $500k property",
            intent=QueryIntent.CALCULATION,
            complexity=Complexity.MEDIUM,
            requires_computation=True,
            tools_needed=[Tool.MORTGAGE_CALC],
        )
        assert analysis.should_use_agent() is True

    def test_should_use_agent_requires_comparison(self):
        """Queries requiring comparison should use agent."""
        analysis = QueryAnalysis(
            query="Compare property A and property B",
            intent=QueryIntent.COMPARISON,
            complexity=Complexity.MEDIUM,
            requires_comparison=True,
            tools_needed=[Tool.RAG_RETRIEVAL, Tool.COMPARATOR],
        )
        assert analysis.should_use_agent() is True

    def test_should_use_agent_multiple_tools(self):
        """Queries needing multiple tools should use agent."""
        analysis = QueryAnalysis(
            query="Find apartments and calculate mortgage for each",
            intent=QueryIntent.FILTERED_SEARCH,
            complexity=Complexity.MEDIUM,
            tools_needed=[Tool.RAG_RETRIEVAL, Tool.MORTGAGE_CALC],
        )
        assert analysis.should_use_agent() is True

    def test_should_use_rag_only_simple_retrieval(self):
        """Simple retrieval should use RAG only."""
        analysis = QueryAnalysis(
            query="Show me apartments in Krakow",
            intent=QueryIntent.SIMPLE_RETRIEVAL,
            complexity=Complexity.SIMPLE,
            requires_computation=False,
            requires_comparison=False,
            tools_needed=[Tool.RAG_RETRIEVAL],
        )
        assert analysis.should_use_rag_only() is True

    def test_should_not_use_rag_only_if_computation_needed(self):
        """RAG-only should be false if computation is needed."""
        analysis = QueryAnalysis(
            query="Calculate average price",
            intent=QueryIntent.ANALYSIS,
            complexity=Complexity.SIMPLE,
            requires_computation=True,
            tools_needed=[Tool.RAG_RETRIEVAL],
        )
        assert analysis.should_use_rag_only() is False

    def test_should_not_use_rag_only_if_multiple_tools(self):
        """RAG-only should be false if multiple tools needed."""
        analysis = QueryAnalysis(
            query="Find and compare apartments",
            intent=QueryIntent.COMPARISON,
            complexity=Complexity.SIMPLE,
            tools_needed=[Tool.RAG_RETRIEVAL, Tool.COMPARATOR],
        )
        assert analysis.should_use_rag_only() is False


class TestHybridAgentDomainGuard:
    """Tests for domain guard functionality."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock hybrid agent for testing domain guard."""
        with (
            patch("agents.hybrid_agent.ConversationalRetrievalChain"),
            patch("agents.hybrid_agent.create_openai_tools_agent"),
            patch("agents.hybrid_agent.AgentExecutor"),
            patch("agents.hybrid_agent.create_property_tools"),
        ):
            from agents.hybrid_agent import HybridPropertyAgent

            mock_llm = MagicMock()
            mock_retriever = MagicMock()
            mock_memory = MagicMock()

            agent = HybridPropertyAgent(
                llm=mock_llm,
                retriever=mock_retriever,
                memory=mock_memory,
                internet_enabled=False,
            )
            return agent

    def test_domain_guard_returns_none_for_normal_queries(self, mock_agent):
        """Normal real estate queries should pass through domain guard."""
        result = mock_agent._domain_guard("Find apartments in Warsaw")
        assert result is None

    def test_domain_guard_handles_capability_questions(self, mock_agent):
        """Capability questions should return help response."""
        queries = [
            "What can you do?",
            "How can you help me?",
            "What are your capabilities?",
            "Help me",
        ]
        for query in queries:
            result = mock_agent._domain_guard(query)
            assert result is not None, f"Expected response for: {query}"
            assert "method" in result
            assert result["method"] == "capabilities"
            assert "Real Estate Assistant" in result["answer"]

    def test_domain_guard_handles_out_of_domain_queries(self, mock_agent):
        """Out-of-domain queries should be rejected."""
        queries = [
            "Give me a cookie recipe",
            "How to cook pizza?",
            "Best cake recipes",
        ]
        for query in queries:
            result = mock_agent._domain_guard(query)
            assert result is not None, f"Expected rejection for: {query}"
            assert result["method"] == "out_of_domain"
            assert "can't help with that" in result["answer"]

    def test_domain_guard_empty_query(self, mock_agent):
        """Empty queries should return None (let normal flow handle)."""
        result = mock_agent._domain_guard("")
        assert result is None

        result = mock_agent._domain_guard("   ")
        assert result is None

    def test_domain_guard_internet_hint_when_enabled(self, mock_agent):
        """Capability response should mention web research when enabled."""
        mock_agent.internet_enabled = True
        result = mock_agent._domain_guard("What can you do?")
        assert "Web research is enabled" in result["answer"]

    def test_domain_guard_internet_hint_when_disabled(self, mock_agent):
        """Capability response should note web is disabled when off."""
        mock_agent.internet_enabled = False
        result = mock_agent._domain_guard("How can you help?")
        assert "Web research is currently disabled" in result["answer"]


class TestHybridAgentProcessQuery:
    """Tests for process_query routing decisions."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock hybrid agent with mocked internals."""
        with (
            patch("agents.hybrid_agent.ConversationalRetrievalChain"),
            patch("agents.hybrid_agent.create_openai_tools_agent"),
            patch("agents.hybrid_agent.AgentExecutor"),
            patch("agents.hybrid_agent.create_property_tools"),
        ):
            from agents.hybrid_agent import HybridPropertyAgent

            mock_llm = MagicMock()
            mock_retriever = MagicMock()

            agent = HybridPropertyAgent(
                llm=mock_llm,
                retriever=mock_retriever,
                internet_enabled=False,
            )

            # Mock the processing methods
            agent._process_with_rag = MagicMock(
                return_value={
                    "answer": "RAG answer",
                    "source_documents": [],
                    "method": "rag",
                    "intent": "simple_retrieval",
                }
            )
            agent._process_with_agent = MagicMock(
                return_value={
                    "answer": "Agent answer",
                    "source_documents": [],
                    "method": "agent",
                    "intent": "calculation",
                }
            )
            agent._process_hybrid = MagicMock(
                return_value={
                    "answer": "Hybrid answer",
                    "source_documents": [],
                    "method": "hybrid",
                    "intent": "analysis",
                }
            )

            return agent

    def test_routes_simple_queries_to_rag(self, mock_agent):
        """Simple retrieval queries should route to RAG."""
        # Mock analyzer to return simple analysis
        mock_agent.analyzer.analyze = MagicMock(
            return_value=QueryAnalysis(
                query="Show me apartments",
                intent=QueryIntent.SIMPLE_RETRIEVAL,
                complexity=Complexity.SIMPLE,
                tools_needed=[Tool.RAG_RETRIEVAL],
            )
        )

        _result = mock_agent.process_query("Show me apartments")

        mock_agent._process_with_rag.assert_called_once()
        mock_agent._process_with_agent.assert_not_called()

    def test_routes_complex_queries_to_agent(self, mock_agent):
        """Complex queries should route to agent."""
        mock_agent.analyzer.analyze = MagicMock(
            return_value=QueryAnalysis(
                query="Calculate mortgage and compare properties",
                intent=QueryIntent.CALCULATION,
                complexity=Complexity.COMPLEX,
                requires_computation=True,
                tools_needed=[Tool.MORTGAGE_CALC, Tool.COMPARATOR],
            )
        )

        _result = mock_agent.process_query("Calculate mortgage and compare properties")

        mock_agent._process_with_agent.assert_called_once()
        mock_agent._process_with_rag.assert_not_called()

    def test_routes_medium_queries_to_hybrid(self, mock_agent):
        """Medium complexity queries should route to hybrid approach."""
        mock_agent.analyzer.analyze = MagicMock(
            return_value=QueryAnalysis(
                query="What's the average price in Warsaw?",
                intent=QueryIntent.ANALYSIS,
                complexity=Complexity.MEDIUM,
                tools_needed=[Tool.RAG_RETRIEVAL],
            )
        )

        _result = mock_agent.process_query("What's the average price in Warsaw?")

        mock_agent._process_hybrid.assert_called_once()

    def test_web_search_disabled_returns_message(self, mock_agent):
        """Queries requiring web search should return disabled message when internet off."""
        mock_agent.internet_enabled = False
        mock_agent.analyzer.analyze = MagicMock(
            return_value=QueryAnalysis(
                query="What are current mortgage rates?",
                intent=QueryIntent.GENERAL_QUESTION,
                complexity=Complexity.SIMPLE,
                requires_external_data=True,
                tools_needed=[Tool.WEB_SEARCH],
            )
        )

        result = mock_agent.process_query("What are current mortgage rates?")

        assert result["method"] == "web_search_disabled"
        assert "internet tools are disabled" in result["answer"]

    def test_includes_analysis_when_requested(self, mock_agent):
        """Analysis should be included when return_analysis=True."""
        mock_agent.analyzer.analyze = MagicMock(
            return_value=QueryAnalysis(
                query="Show me apartments",
                intent=QueryIntent.SIMPLE_RETRIEVAL,
                complexity=Complexity.SIMPLE,
                tools_needed=[Tool.RAG_RETRIEVAL],
            )
        )

        result = mock_agent.process_query("Show me apartments", return_analysis=True)

        assert "analysis" in result

    def test_domain_guard_takes_precedence(self, mock_agent):
        """Domain guard responses should bypass normal routing."""
        result = mock_agent.process_query("What can you do?")

        assert result["method"] == "capabilities"
        mock_agent._process_with_rag.assert_not_called()
        mock_agent._process_with_agent.assert_not_called()


class TestCreateHybridAgentFactory:
    """Tests for create_hybrid_agent factory function."""

    def test_creates_hybrid_agent_with_tools(self):
        """Factory should create HybridPropertyAgent when use_tools=True."""
        with (
            patch("agents.hybrid_agent.ConversationalRetrievalChain"),
            patch("agents.hybrid_agent.create_openai_tools_agent"),
            patch("agents.hybrid_agent.AgentExecutor"),
            patch("agents.hybrid_agent.create_property_tools"),
        ):
            from agents.hybrid_agent import HybridPropertyAgent, create_hybrid_agent

            mock_llm = MagicMock()
            mock_retriever = MagicMock()

            agent = create_hybrid_agent(
                llm=mock_llm,
                retriever=mock_retriever,
                use_tools=True,
            )

            assert isinstance(agent, HybridPropertyAgent)

    def test_creates_simple_rag_agent_without_tools(self):
        """Factory should create SimpleRAGAgent when use_tools=False."""
        with patch("agents.hybrid_agent.ConversationalRetrievalChain"):
            from agents.hybrid_agent import SimpleRAGAgent, create_hybrid_agent

            mock_llm = MagicMock()
            mock_retriever = MagicMock()

            agent = create_hybrid_agent(
                llm=mock_llm,
                retriever=mock_retriever,
                use_tools=False,
            )

            assert isinstance(agent, SimpleRAGAgent)
