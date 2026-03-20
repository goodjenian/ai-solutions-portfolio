from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_ci_parity_script_dry_run_prints_expected_steps() -> None:
    # Navigate from apps/api/tests/integration/ to repo root (4 levels up)
    repo_root = Path(__file__).resolve().parents[4]
    script_path = repo_root / "scripts" / "ci" / "ci_parity.py"
    result = subprocess.run(
        [sys.executable, str(script_path), "--dry-run"],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(repo_root),  # Script expects to run from repo root
    )
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "RUN:" in out
    assert "ruff check" in out
    assert "mypy" in out
    assert "bandit" in out
    assert "pip_audit" in out
    assert "pytest" in out
    assert "coverage_gate.py" in out
