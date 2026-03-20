from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_compose_smoke_script_dry_run(tmp_path: Path):
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text("version: '3.8'\nservices: {}\n", encoding="utf-8")

    # Navigate from apps/api/tests/integration/ to repo root (4 levels up)
    repo_root = Path(__file__).resolve().parents[4]
    script_path = repo_root / "scripts" / "docker" / "compose_smoke.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--compose-file",
            str(compose_file),
            "--dry-run",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "UP:" in result.stdout
    assert "docker compose -f" in result.stdout
    assert "CHECK:" in result.stdout
    assert "CHECK_AUTH:" in result.stdout
