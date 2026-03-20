from __future__ import annotations

import sys  # noqa: E402
from pathlib import Path

import pytest  # noqa: E402

# Add project root to Python path for scripts imports (top-level, before any test imports)
# From apps/api/tests/unit/ to project root: 4 levels up
_project_root = Path(__file__).resolve().parents[4]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.security.forbidden_tokens import main as forbidden_tokens_main  # noqa: E402


def test_forbidden_tokens_check_passes_when_no_tokens_present(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("hello\nworld\n", encoding="utf-8")
    assert forbidden_tokens_main(["--root", str(tmp_path)]) == 0


def test_forbidden_tokens_check_fails_when_token_present(tmp_path: Path) -> None:
    (tmp_path / "b.txt").write_text("x=NEXT_PUBLIC_API_KEY\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        forbidden_tokens_main(["--root", str(tmp_path)])


def test_forbidden_tokens_check_ignores_node_modules(tmp_path: Path) -> None:
    node_modules = tmp_path / "node_modules"
    node_modules.mkdir(parents=True)
    (node_modules / "c.txt").write_text("NEXT_PUBLIC_API_KEY\n", encoding="utf-8")
    assert forbidden_tokens_main(["--root", str(tmp_path)]) == 0


def test_forbidden_tokens_check_scans_only_selected_paths(tmp_path: Path) -> None:
    ok = tmp_path / "ok.txt"
    bad = tmp_path / "bad.txt"
    ok.write_text("hello\n", encoding="utf-8")
    bad.write_text("NEXT_PUBLIC_API_KEY\n", encoding="utf-8")
    assert forbidden_tokens_main(["--root", str(tmp_path), str(ok)]) == 0


def test_forbidden_tokens_check_all_overrides_paths(tmp_path: Path) -> None:
    ok = tmp_path / "ok.txt"
    bad = tmp_path / "bad.txt"
    ok.write_text("hello\n", encoding="utf-8")
    bad.write_text("NEXT_PUBLIC_API_KEY\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        forbidden_tokens_main(["--root", str(tmp_path), "--all", str(ok)])
