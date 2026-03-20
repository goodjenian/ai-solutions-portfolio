from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add project root to Python path for scripts imports (before any test imports)
# From apps/api/tests/unit/ to project root: 4 levels up
_project_root = Path(__file__).resolve().parents[4]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.ci.ci_parity import (  # noqa: E402
    ParityConfig,
    build_commands,
    build_integration_diff_coverage_gate_cmd,
    build_unit_diff_coverage_gate_cmd,
    format_command,
    parse_args,
)


def test_parse_args_defaults_run_unit_and_integration() -> None:
    cfg = parse_args([])
    assert cfg.run_unit is True
    assert cfg.run_integration is True
    assert cfg.dry_run is False
    assert cfg.python_exe


def test_parse_args_unit_only_disables_integration() -> None:
    cfg = parse_args(["--unit-only"])
    assert cfg.run_unit is True
    assert cfg.run_integration is False


def test_parse_args_integration_only_disables_unit() -> None:
    cfg = parse_args(["--integration-only"])
    assert cfg.run_unit is False
    assert cfg.run_integration is True


def test_build_unit_diff_coverage_gate_cmd_includes_base_ref_when_provided() -> None:
    cmd = build_unit_diff_coverage_gate_cmd("python", base_ref="origin/main")
    assert "--base-ref" in cmd
    assert "origin/main" in cmd


def test_build_unit_diff_coverage_gate_cmd_omits_base_ref_when_missing() -> None:
    cmd = build_unit_diff_coverage_gate_cmd("python", base_ref=None)
    assert "--base-ref" not in cmd


def test_build_integration_diff_coverage_gate_cmd_includes_base_ref_when_provided() -> None:
    cmd = build_integration_diff_coverage_gate_cmd("python", base_ref="origin/main")
    assert "--base-ref" in cmd
    assert "origin/main" in cmd


def test_format_command_returns_string() -> None:
    assert isinstance(format_command([sys.executable, "-c", "print('x')"]), str)


def test_build_commands_includes_security_audits() -> None:
    cfg = ParityConfig(
        python_exe=sys.executable,
        base_ref=None,
        run_unit=False,
        run_integration=False,
        dry_run=True,
    )
    cmds = build_commands(cfg)
    flat = " ".join(" ".join(cmd) for cmd in cmds)
    assert "bandit" in flat
    assert "pip_audit" in flat


def test_main_dry_run_prints_security_steps(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from scripts.ci import ci_parity

    # Don't mock Path.exists - let it detect we're already in apps/api
    rc = ci_parity.main(["--dry-run", "--unit-only"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "RUN:" in out
    assert "bandit" in out
    assert "pip_audit" in out


def test_main_raises_when_not_run_from_repo_root(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.ci import ci_parity

    original_exists = Path.exists

    def fake_exists(self: Path) -> bool:
        if str(self).replace("\\", "/") == "scripts/ci/coverage_gate.py":
            return False
        result = original_exists(self)
        # Path.exists returns object (bool in practice), but mypy sees it as object
        assert isinstance(result, bool)
        return result

    monkeypatch.setattr(Path, "exists", fake_exists)
    with pytest.raises(FileNotFoundError, match="coverage_gate.py"):
        ci_parity.main([])


@pytest.mark.parametrize(
    ("run_unit", "run_integration", "expected_contains"),
    [
        (True, True, ("tests/unit", "tests/integration")),
        (True, False, ("tests/unit",)),
        (False, True, ("tests/integration",)),
    ],
)
def test_build_commands_includes_expected_test_scopes(
    run_unit: bool, run_integration: bool, expected_contains: tuple[str, ...]
) -> None:
    cfg = ParityConfig(
        python_exe=sys.executable,
        base_ref=None,
        run_unit=run_unit,
        run_integration=run_integration,
        dry_run=True,
    )
    cmds = build_commands(cfg)
    flat = " ".join(" ".join(cmd) for cmd in cmds)
    for token in expected_contains:
        assert token in flat
