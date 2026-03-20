from __future__ import annotations

from pathlib import Path


def test_ci_workflow_has_no_mvp_disable_flag() -> None:
    # Navigate from apps/api/tests/unit/ to repo root (4 levels up: unit -> tests -> api -> project root)
    repo_root = Path(__file__).resolve().parents[4]
    workflow = repo_root / ".github" / "workflows" / "ci.yml"

    text = workflow.read_text(encoding="utf-8")

    assert "MVP_CI_DISABLED" not in text
    assert "env.MVP_CI_DISABLED" not in text
    assert "CI disabled notice" not in text
