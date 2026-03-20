from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_dev_start_script_dry_run_does_not_print_secrets() -> None:
    # Navigate from apps/api/tests/integration/ to repo root (4 levels up)
    repo_root = Path(__file__).resolve().parents[4]
    script_path = repo_root / "scripts" / "start.py"
    result = subprocess.run(
        [sys.executable, str(script_path), "--mode", "local", "--dry-run"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "BACKEND_CMD:" in out
    assert "FRONTEND_CMD:" in out
    assert "dev-secret-key" not in out
    assert "<redacted>" in out
