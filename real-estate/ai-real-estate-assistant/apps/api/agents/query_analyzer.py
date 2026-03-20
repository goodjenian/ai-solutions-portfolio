"""
Query analyzer for classifying user intent and complexity.

This module analyzes user queries to determine:
- Query intent (retrieval, analysis, comparison, calculation)
- Complexity level (simple, medium, complex)
- Required tools
- Optimal routing strategy
"""

import re
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class QueryIntent(str, Enum):
    """Types of query intents."""

    SIMPLE_RETRIEVAL = "simple_retrieval"  # "Show me apartments in Krakow"
    FILTERED_SEARCH = "filtered_search"  # "Find 2-bed apartments under $1000"
    COMPARISON = "comparison"  # "Compare properties in Warsaw vs Krakow"
    ANALYSIS = "analysis"  # "What's the average price per sqm?"
    CALCULATION = "calculation"  # "Calculate mortgage for $200k property"
    RECOMMENDATION = "recommendation"  # "What's the best value for money?"
    CONVERSATION = "conversation"  # "Tell me more about the last property"
    GENERAL_QUESTION = "general_question"  # "How does the rental market work?"


class Complexity(str, Enum):
    """Query complexity levels."""

    SIMPLE = "simple"  # Direct retrieval, can use RAG only
    MEDIUM = "medium"  # Some filtering or simple computation
    COMPLEX = "complex"  # Requires multiple steps, tools, or reasoning


class Tool(str, Enum):
    """Available tools for query processing."""

    RAG_RETRIEVAL = "rag_retrieval"
    PYTHON_CODE = "python_code"
    CALCULATOR = "calculator"
    COMPARATOR = "comparator"
    WEB_SEARCH = "web_search"
    MORTGAGE_CALC = "mortgage_calculator"


class QueryAnalysis(BaseModel):
    """Analysis result for a query."""

    query: str
    intent: QueryIntent
    complexity: Complexity
    requires_computation: bool = False
    requires_comparison: bool = False
    requires_external_data: bool = False
    tools_needed: List[Tool] = Field(default_factory=list)
    extracted_filters: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reasoning: Optional[str] = None

    def should_use_agent(self) -> bool:
        """Determine if query needs agent-based processing."""
        return (
            self.complexity == Complexity.COMPLEX
            or self.requires_computation
            or self.requires_comparison
            or len(self.tools_needed) > 1
        )

    def should_use_rag_only(self) -> bool:
        """Determine if query can be handled by RAG alone."""
        return (
            self.complexity == Complexity.SIMPLE
            and not self.requires_computation
            and not self.requires_comparison
            and Tool.RAG_RETRIEVAL in self.tools_needed
            and len(self.tools_needed) == 1
        )


class QueryAnalyzer:
    """
    Analyzer for classifying queries and determining optimal processing strategy.

    This uses pattern matching and heuristics to classify queries without
    requiring an LLM call (fast and cost-effective).
    """

    # Keywords for intent classification
    RETRIEVAL_KEYWORDS = [
        "show",
        "find",
        "list",
        "search",
        "get",
        "display",
        "want",
        "need",
        "looking for",
        "give me",
        "показать",
        "найти",
        "список",
        "поиск",
        "дать",  # RU
        "göster",
        "bul",
        "listele",
        "ara",
        "ver",
        "istiyorum",  # TR
    ]

    COMPARISON_KEYWORDS = [
        "compare",
        "versus",
        "vs",
        "difference",
        "between",
        "better",
        "cheaper",
        "more expensive",
        "bigger",
        "smaller",
        "сравнить",
        "против",
        "разница",
        "между",
        "лучше",
        "дешевле",  # RU
        "karşılaştır",
        "fark",
        "arasında",
        "daha iyi",
        "daha ucuz",  # TR
    ]

    CALCULATION_KEYWORDS = [
        "calculate",
        "compute",
        "how much",
        "total cost",
        "monthly payment",
        "mortgage",
        "interest",
        "loan",
        "рассчитать",
        "посчитать",
        "сколько",
        "ипотека",
        "кредит",  # RU
        "hesapla",
        "ne kadar",
        "toplam",
        "kredi",
        "ipotek",  # TR
    ]

    ANALYSIS_KEYWORDS = [
        "average",
        "mean",
        "median",
        "statistics",
        "trend",
        "distribution",
        "analyze",
        "analysis",
        "insights",
        "средняя",
        "медиана",
        "статистика",
        "тренд",
        "анализ",  # RU
        "ortalama",
        "medyan",
        "istatistik",
        "trend",
        "analiz",  # TR
    ]

    RECOMMENDATION_KEYWORDS = [
        "recommend",
        "suggest",
        "best",
        "optimal",
        "top",
        "ideal",
        "perfect",
        "most suitable",
        "порекомендуй",
        "лучший",
        "топ",
        "идеальный",  # RU
        "öner",
        "tavsiye",
        "en iyi",
        "ideal",
        "mükemmel",  # TR
    ]

    # Filter extraction patterns
    # Price: match currency symbols or explicitly "price"/"cost" context if just number
    # For now, keeping simple but avoiding 4-digit years in specific ranges if possible?
    # Actually, let's keep the pattern but filter results later.
    PRICE_PATTERN = re.compile(r"\$?\d{1,5}(?:,\d{3})*(?:\.\d{2})?")
    ROOMS_PATTERN = re.compile(r"(\d+)[- ](?:bed(?:room)?|room|комнат|odalı)")
    CITY_PATTERN = re.compile(
        r"\b(warsaw|krakow|gdansk|wroclaw|poznan|warszawa|kraków|gdańsk|wrocław|poznań|варшав|краков|гданьск|вроцлав|познан|varşova)\w*",
        re.IGNORECASE,
    )
    # Added 'построен' (built) and 'yapı' (building/built) stems
    YEAR_PATTERN = re.compile(
        r"(?:built|year|год|yıl|построен|yapı)[\D]{0,10}(\d{4})", re.IGNORECASE
    )
    # Allow suffixes on class/rating words (e.g. sınıf-ı, класс-а)
    ENERGY_PATTERN = re.compile(
        r"(?:energy|epc|энергия|enerji)(?:\s+(?:class|rating|класс|sınıf)\w*)?\s+([A-G])\b",
        re.IGNORECASE,
    )

    # City normalization map
    CITY_VARIANTS = {
        "Warsaw": ["warsaw", "warszawa", "варшав", "varşova"],
        "Krakow": ["krakow", "kraków", "краков"],
        "Gdansk": ["gdansk", "gdańsk", "гданьск"],
        "Wroclaw": ["wroclaw", "wrocław", "вроцлав"],
        "Poznan": ["poznan", "poznań", "познан"],
    }

    # Multilingual Amenities - using stems for better matching
    PARKING_KEYWORDS = {
        "parking",
        "garage",
        "парковк",
        "гараж",
        "otopark",
        "garaj",
    }  # парковк(а/и/ой)
    GARDEN_KEYWORDS = {"garden", "yard", "сад", "двор", "bahçe"}
    POOL_KEYWORDS = {"pool", "бассейн", "havuz"}
    FURNISHED_KEYWORDS = {"furnished", "мебель", "меблир", "eşyalı", "mobilyalı"}  # меблир(ованная)
    ELEVATOR_KEYWORDS = {"elevator", "lift", "лифт", "asansör", "winda"}

    def analyze(self, query: str) -> QueryAnalysis:
        """
        Analyze a query and return classification.

        Args:
            query: User query string

        Returns:
            QueryAnalysis with intent, complexity, and tools
        """
        query_lower = query.lower()

        # Determine intent
        intent = self._classify_intent(query_lower)

        # Extract filters
        filters = self._extract_filters(query)

        # Determine complexity
        complexity = self._determine_complexity(query_lower, intent, filters)

        # Determine required tools
        tools = self._determine_tools(intent, complexity, query_lower)

        # Check for special requirements
        requires_computation = self._requires_computation(query_lower, intent)
        requires_comparison = intent == QueryIntent.COMPARISON
        requires_external_data = self._requires_external_data(query_lower)

        # Build analysis
        analysis = QueryAnalysis(
            query=query,
            intent=intent,
            complexity=complexity,
            requires_computation=requires_computation,
            requires_comparison=requires_comparison,
            requires_external_data=requires_external_data,
            tools_needed=tools,
            extracted_filters=filters,
            reasoning=self._generate_reasoning(intent, complexity, tools),
        )

        return analysis

    def _classify_intent(self, query_lower: str) -> QueryIntent:
        """Classify the primary intent of the query."""

        # Check for comparison
        if any(kw in query_lower for kw in self.COMPARISON_KEYWORDS):
            return QueryIntent.COMPARISON

        # Check for calculation
        if any(kw in query_lower for kw in self.CALCULATION_KEYWORDS):
            return QueryIntent.CALCULATION

        # Check for analysis
        if any(kw in query_lower for kw in self.ANALYSIS_KEYWORDS):
            return QueryIntent.ANALYSIS

        # Check for recommendation
        if any(kw in query_lower for kw in self.RECOMMENDATION_KEYWORDS):
            return QueryIntent.RECOMMENDATION

        # Check for conversation (use word boundaries to avoid false matches like "it" in "with")
        conversation_patterns = [
            r"\bprevious\b",
            r"\blast\b",
            r"\bthat one\b",
            r"\bit\b",
            r"\bthis\b",
        ]
        if any(re.search(pattern, query_lower) for pattern in conversation_patterns):
            return QueryIntent.CONVERSATION

        # Check for filtered search (has specific criteria)
        if any(word in query_lower for word in ["with", "under", "over", "between", "at least"]):
            return QueryIntent.FILTERED_SEARCH

        # Check for simple retrieval
        if any(kw in query_lower for kw in self.RETRIEVAL_KEYWORDS):
            return QueryIntent.SIMPLE_RETRIEVAL

        # Default to general question
        return QueryIntent.GENERAL_QUESTION

    def _extract_filters(self, query: str) -> Dict[str, Any]:
        """Extract structured filters from query."""
        filters: Dict[str, Any] = {}

        # Extract year
        year_match = self.YEAR_PATTERN.search(query)
        year_val = None
        if year_match:
            year_val = int(year_match.group(1))
            filters["year_built_min"] = year_val

        # Extract price
        prices = self.PRICE_PATTERN.findall(query)
        if prices:
            # Clean and convert
            price_values = []
            for p in prices:
                try:
                    val = float(p.replace("$", "").replace(",", ""))
                    # Filter out the year value if it was captured as a price
                    if year_val and abs(val - year_val) < 0.1:
                        continue
                    price_values.append(val)
                except ValueError:
                    continue

            if len(price_values) == 1:
                filters["max_price"] = price_values[0]
            elif len(price_values) >= 2:
                filters["min_price"] = min(price_values)
                filters["max_price"] = max(price_values)

        # Extract number of rooms
        rooms_match = self.ROOMS_PATTERN.search(query)
        if rooms_match:
            filters["rooms"] = int(rooms_match.group(1))

        # Extract city
        city_match = self.CITY_PATTERN.search(query)
        if city_match:
            city_str = city_match.group(0).lower()
            found_city = None
            for canonical, variants in self.CITY_VARIANTS.items():
                if any(v in city_str for v in variants):
                    found_city = canonical
                    break

            if found_city:
                filters["city"] = found_city
            else:
                filters["city"] = city_match.group(1).title()

        # Extract amenities
        query_lower = query.lower()
        if any(kw in query_lower for kw in self.PARKING_KEYWORDS):
            filters["has_parking"] = True
            filters["must_have_parking"] = True
        if any(kw in query_lower for kw in self.GARDEN_KEYWORDS):
            filters["has_garden"] = True
        if any(kw in query_lower for kw in self.POOL_KEYWORDS):
            filters["has_pool"] = True
        if any(kw in query_lower for kw in self.FURNISHED_KEYWORDS):
            filters["is_furnished"] = True
        if any(kw in query_lower for kw in self.ELEVATOR_KEYWORDS):
            filters["must_have_elevator"] = True
            filters["has_elevator"] = True

        # Extract energy
        energy_match = self.ENERGY_PATTERN.search(query)
        if energy_match:
            filters["energy_ratings"] = [energy_match.group(1).upper()]

        return filters

    def _determine_complexity(
        self, query_lower: str, intent: QueryIntent, filters: Dict[str, Any]
    ) -> Complexity:
        """Determine query complexity level."""

        # Complex intents
        if intent in [QueryIntent.ANALYSIS, QueryIntent.COMPARISON, QueryIntent.CALCULATION]:
            return Complexity.COMPLEX

        # Multiple filters = medium complexity
        if len(filters) >= 3:
            return Complexity.MEDIUM

        # Recommendation needs reasoning
        if intent == QueryIntent.RECOMMENDATION:
            return Complexity.COMPLEX

        # Questions requiring explanation (use word boundaries to avoid false matches like "show" matching "how")
        question_patterns = [r"\bwhy\b", r"\bhow\b", r"\bexplain\b", r"\bwhat is\b"]
        if any(re.search(pattern, query_lower) for pattern in question_patterns):
            return Complexity.MEDIUM

        # Simple retrieval
        return Complexity.SIMPLE

    def _determine_tools(
        self, intent: QueryIntent, complexity: Complexity, query_lower: str
    ) -> List[Tool]:
        """Determine which tools are needed."""
        tools = []

        # RAG is almost always needed
        if intent in [
            QueryIntent.SIMPLE_RETRIEVAL,
            QueryIntent.FILTERED_SEARCH,
            QueryIntent.CONVERSATION,
            QueryIntent.RECOMMENDATION,
        ]:
            tools.append(Tool.RAG_RETRIEVAL)

        # Comparison tool
        if intent == QueryIntent.COMPARISON:
            tools.extend([Tool.RAG_RETRIEVAL, Tool.COMPARATOR])

        # Calculation tools
        if intent == QueryIntent.CALCULATION:
            if "mortgage" in query_lower:
                tools.append(Tool.MORTGAGE_CALC)
            else:
                tools.append(Tool.CALCULATOR)

        # Analysis requires Python code execution
        if intent == QueryIntent.ANALYSIS:
            tools.extend([Tool.RAG_RETRIEVAL, Tool.PYTHON_CODE])

        # Web search for external data
        if any(
            kw in query_lower
            for kw in [
                "current",
                "currently",
                "latest",
                "market",
                "today",
                "news",
                "right now",
                "at the moment",
                "сейчас",
                "сегодня",
                "прямо сейчас",
                "актуал",
                "новост",
                "текущ",
                "рынок",
                "ставк",
            ]
        ):
            tools.append(Tool.WEB_SEARCH)

        # Default to RAG if no tools determined
        if not tools:
            tools.append(Tool.RAG_RETRIEVAL)

        return tools

    def _requires_computation(self, query_lower: str, intent: QueryIntent) -> bool:
        """Check if query requires numerical computation."""
        return intent in [QueryIntent.CALCULATION, QueryIntent.ANALYSIS] or any(
            word in query_lower
            for word in [
                "average",
                "mean",
                "sum",
                "total",
                "calculate",
                "compute",
                "percentage",
                "ratio",
            ]
        )

    def _requires_external_data(self, query_lower: str) -> bool:
        """Check if query needs external/current data."""
        return any(
            word in query_lower
            for word in [
                "current",
                "currently",
                "latest",
                "recent",
                "today",
                "market rate",
                "interest rate",
                "news",
                "right now",
                "at the moment",
                "сейчас",
                "сегодня",
                "прямо сейчас",
                "последн",
                "актуал",
                "новост",
                "текущ",
                "рынок",
                "ставк",
            ]
        )

    def _generate_reasoning(
        self, intent: QueryIntent, complexity: Complexity, tools: List[Tool]
    ) -> str:
        """Generate human-readable reasoning for the classification."""
        reasoning_parts = [
            f"Classified as {intent.value}",
            f"Complexity: {complexity.value}",
        ]

        if len(tools) > 0:
            tool_names = [t.value for t in tools]
            reasoning_parts.append(f"Tools: {', '.join(tool_names)}")

        return ". ".join(reasoning_parts)


# Singleton instance
_analyzer = None


def get_query_analyzer() -> QueryAnalyzer:
    """Get or create query analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = QueryAnalyzer()
    return _analyzer


def analyze_query(query: str) -> QueryAnalysis:
    """
    Convenience function to analyze a query.

    Args:
        query: User query string

    Returns:
        QueryAnalysis result
    """
    analyzer = get_query_analyzer()
    return analyzer.analyze(query)
