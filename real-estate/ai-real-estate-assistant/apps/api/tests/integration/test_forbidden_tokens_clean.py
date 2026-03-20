from __future__ import annotations

import sys  # noqa: E402
from pathlib import Path

# Add project root to Python path for scripts imports (top-level, before any test imports)
# From apps/api/tests/integration/ to project root: 4 levels up
_project_root = Path(__file__).resolve().parents[4]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.security.forbidden_tokens import main as forbidden_tokens_main  # noqa: E402


def test_no_forbidden_tokens_in_repo() -> None:
    project_root = Path(__file__).resolve().parents[2]
    assert forbidden_tokens_main(["--root", str(project_root)]) == 0
