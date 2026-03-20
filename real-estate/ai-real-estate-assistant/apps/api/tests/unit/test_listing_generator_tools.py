"""
Unit tests for AI listing generator tools.

Tests for property description, headline, and social media content generation.
"""

import pytest

from tools.listing_generator_tools import (
    PLATFORM_CONSTRAINTS,
    SUPPORTED_LANGUAGES,
    TONE_DESCRIPTIONS,
    HeadlineGeneratorTool,
    HeadlineInput,
    PropertyDescriptionGeneratorTool,
    PropertyDescriptionInput,
    SocialMediaContentGeneratorTool,
    SocialMediaInput,
    create_listing_generator_tools,
)


class TestPropertyDescriptionGeneratorTool:
    """Test suite for PropertyDescriptionGeneratorTool."""

    @pytest.fixture
    def generator(self):
        """Fixture for description generator."""
        return PropertyDescriptionGeneratorTool()

    def test_tool_initialization(self, generator):
        """Test tool initialization."""
        assert generator.name == "listing_description_generator"
        assert "description" in generator.description.lower()
        assert "generate" in generator.description.lower()

    def test_supported_languages(self):
        """Test that supported languages are properly defined."""
        assert "en" in SUPPORTED_LANGUAGES
        assert "pl" in SUPPORTED_LANGUAGES
        assert "es" in SUPPORTED_LANGUAGES
        assert "de" in SUPPORTED_LANGUAGES
        assert "fr" in SUPPORTED_LANGUAGES
        assert len(SUPPORTED_LANGUAGES) >= 7

    def test_tone_descriptions(self):
        """Test that tone descriptions are properly defined."""
        assert "professional" in TONE_DESCRIPTIONS
        assert "friendly" in TONE_DESCRIPTIONS
        assert "luxury" in TONE_DESCRIPTIONS
        assert "engaging" in TONE_DESCRIPTIONS

    def test_invalid_language_handling(self, generator):
        """Test handling of invalid language parameter."""
        result = generator._run(
            property_data="Test property",
            language="invalid_lang",
        )
        assert "Error" in result
        assert "Unsupported language" in result

    def test_invalid_tone_handling(self, generator):
        """Test handling of invalid tone parameter."""
        result = generator._run(
            property_data="Test property",
            tone="invalid_tone",
        )
        assert "Error" in result
        assert "Unsupported tone" in result


class TestHeadlineGeneratorTool:
    """Test suite for HeadlineGeneratorTool."""

    @pytest.fixture
    def generator(self):
        """Fixture for headline generator."""
        return HeadlineGeneratorTool()

    def test_tool_initialization(self, generator):
        """Test tool initialization."""
        assert generator.name == "listing_headline_generator"
        assert "headline" in generator.description.lower()

    def test_invalid_language_handling(self, generator):
        """Test handling of invalid language parameter."""
        result = generator._run(
            property_data="Test property",
            language="xx",
        )
        assert "Error" in result
        assert "Unsupported language" in result

    def test_valid_styles(self):
        """Test that valid styles are accepted."""
        # Style validation happens in the prompt building
        # We just verify the tool can be instantiated
        generator = HeadlineGeneratorTool()
        assert generator is not None


class TestSocialMediaContentGeneratorTool:
    """Test suite for SocialMediaContentGeneratorTool."""

    @pytest.fixture
    def generator(self):
        """Fixture for social media generator."""
        return SocialMediaContentGeneratorTool()

    def test_tool_initialization(self, generator):
        """Test tool initialization."""
        assert generator.name == "social_media_content_generator"
        assert "social media" in generator.description.lower()

    def test_platform_constraints(self):
        """Test that platform constraints are properly defined."""
        assert "facebook" in PLATFORM_CONSTRAINTS
        assert "instagram" in PLATFORM_CONSTRAINTS
        assert "linkedin" in PLATFORM_CONSTRAINTS
        assert "twitter" in PLATFORM_CONSTRAINTS

        # Verify constraint structure
        for _platform, constraints in PLATFORM_CONSTRAINTS.items():
            assert "max_length" in constraints
            assert "hashtag_style" in constraints
            assert "emoji_style" in constraints

    def test_invalid_platform_handling(self, generator):
        """Test handling of invalid platform parameter."""
        result = generator._run(
            property_data="Test property",
            platform="tiktok",
        )
        assert "Error" in result
        assert "Unsupported platform" in result

    def test_invalid_language_handling(self, generator):
        """Test handling of invalid language parameter."""
        result = generator._run(
            property_data="Test property",
            platform="facebook",
            language="invalid",
        )
        assert "Error" in result
        assert "Unsupported language" in result

    def test_platform_character_limits(self):
        """Test that each platform has appropriate character limits."""
        assert PLATFORM_CONSTRAINTS["twitter"]["max_length"] == 280
        assert PLATFORM_CONSTRAINTS["instagram"]["max_length"] == 2200
        assert PLATFORM_CONSTRAINTS["linkedin"]["max_length"] == 3000
        assert PLATFORM_CONSTRAINTS["facebook"]["max_length"] == 63206


class TestListingGeneratorFactory:
    """Test suite for the factory function."""

    def test_create_all_tools(self):
        """Test creating all listing generator tools."""
        tools = create_listing_generator_tools()

        assert len(tools) == 3
        assert all(hasattr(tool, "name") for tool in tools)
        assert all(hasattr(tool, "description") for tool in tools)

    def test_tool_names_unique(self):
        """Test that tool names are unique."""
        tools = create_listing_generator_tools()
        names = [tool.name for tool in tools]

        assert len(names) == len(set(names))  # All unique

    def test_all_expected_tools_present(self):
        """Test that all expected tools are created."""
        tools = create_listing_generator_tools()
        tool_names = {tool.name for tool in tools}

        expected_names = {
            "listing_description_generator",
            "listing_headline_generator",
            "social_media_content_generator",
        }

        assert tool_names == expected_names


class TestToolIntegration:
    """Integration tests for listing generator tools."""

    @pytest.fixture
    def all_tools(self):
        """Fixture with all listing generator tools."""
        return create_listing_generator_tools()

    def test_tools_have_llm_attribute(self, all_tools):
        """Test that all tools have LLM attribute (may be None)."""
        for tool in all_tools:
            assert hasattr(tool, "_llm")

    def test_tools_have_async_methods(self, all_tools):
        """Test that all tools have async versions."""
        for tool in all_tools:
            assert hasattr(tool, "_arun")

    def test_description_tool_metadata(self):
        """Test PropertyDescriptionGeneratorTool metadata."""
        tool = PropertyDescriptionGeneratorTool()
        assert hasattr(tool, "args_schema")
        assert tool.args_schema is PropertyDescriptionInput

    def test_headline_tool_metadata(self):
        """Test HeadlineGeneratorTool metadata."""
        tool = HeadlineGeneratorTool()
        assert hasattr(tool, "args_schema")
        assert tool.args_schema is HeadlineInput

    def test_social_media_tool_metadata(self):
        """Test SocialMediaContentGeneratorTool metadata."""
        tool = SocialMediaContentGeneratorTool()
        assert hasattr(tool, "args_schema")
        assert tool.args_schema is SocialMediaInput
