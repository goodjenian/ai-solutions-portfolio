"""
Test script to verify the Agent System.
"""

import logging
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

from rules.engine import RuleEngine

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Skip if legacy dev agents are not present
pytest.importorskip("agents.dev.base")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SystemTest")


def test_rule_engine():
    logger.info("Testing Rule Engine...")
    engine = RuleEngine()

    # Test 1: Good code
    good_code = "def hello():\n    return 'world'"
    violations = engine.validate_code(good_code)
    assert len(violations) == 0, f"Expected 0 violations, got {len(violations)}"
    logger.info("Good code passed.")

    # Test 2: Bad code (Secret)
    bad_code = "API_KEY = '12345678901234567890'"
    violations = engine.validate_code(bad_code)
    assert len(violations) > 0, "Expected violations for secret"
    logger.info("Secret detection passed.")


@patch("agents.dev.base.ModelProviderFactory")
def test_pipeline_dry_run(mock_factory):
    logger.info("Testing Pipeline (Dry Run / Mock)...")
    pytest.importorskip("agents.dev.coding")
    from workflows.pipeline import DevPipeline

    # Setup Mock Provider
    mock_provider = MagicMock()
    mock_model_info = MagicMock()
    mock_model_info.id = "gpt-mock"
    mock_provider.list_models.return_value = [mock_model_info]

    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = "Mocked Response"
    mock_provider.create_model.return_value = mock_llm

    mock_factory.get_provider.return_value = mock_provider

    try:
        pipeline = DevPipeline()
        logger.info("Pipeline instantiated successfully.")

        # Run a simple task
        result = pipeline.implement_feature("Test Feature")
        logger.info(f"Pipeline Result Status: {result['status']}")

        assert result["status"] == "success"
        assert result["final_output"]["code"] == "Mocked Response"
        logger.info("Pipeline execution verified.")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


@patch("workflows.pipeline.subprocess.run")
@patch("agents.dev.base.ModelProviderFactory")
def test_pipeline_git_integration(mock_factory, mock_subprocess):
    logger.info("Testing Pipeline Git Integration...")
    pytest.importorskip("agents.dev.coding")
    from workflows.pipeline import DevPipeline

    # Setup Mock Provider
    mock_provider = MagicMock()
    mock_model_info = MagicMock()
    mock_model_info.id = "gpt-mock"
    mock_provider.list_models.return_value = [mock_model_info]
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = "Mocked Response"
    mock_provider.create_model.return_value = mock_llm
    mock_factory.get_provider.return_value = mock_provider

    # Setup Mock Subprocess
    mock_subprocess.return_value.stdout = "branch created"
    mock_subprocess.return_value.returncode = 0

    pipeline = DevPipeline()
    result = pipeline.implement_feature("Git Test", use_git=True)

    assert result["status"] == "success"

    # Verify git commands were called
    git_calls = [call[0][0] for call in mock_subprocess.call_args_list]

    has_checkout = any("checkout" in cmd for cmd in git_calls)
    has_commit = any("commit" in cmd for cmd in git_calls)

    assert has_checkout, "Git checkout not called"
    assert has_commit, "Git commit not called"
    logger.info("Git integration verified.")


if __name__ == "__main__":
    test_rule_engine()
    test_pipeline_dry_run()
    test_pipeline_git_integration()
    logger.info("All system tests passed!")
