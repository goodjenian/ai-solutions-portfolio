from __future__ import annotations

import runpy
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from scripts.ci.coverage_gate import (
    critical_coverage_percent,
    diff_coverage_percent,
    load_coverage_xml,
    main,
    parse_changed_lines_from_diff,
)


def _write_coverage_xml(tmp_path: Path, xml: str) -> Path:
    path = tmp_path / "coverage.xml"
    path.write_text(xml, encoding="utf-8")
    return path


def test_parse_changed_lines_from_diff_extracts_added_lines():
    diff_text = "\n".join(
        [
            "diff --git a/api/foo.py b/api/foo.py",
            "--- a/api/foo.py",
            "+++ b/api/foo.py",
            "@@ -0,0 +1,3 @@",
            "+print('a')",
            "+print('b')",
            "+print('c')",
        ]
    )
    changed = parse_changed_lines_from_diff(diff_text)
    assert changed["api/foo.py"] == {1, 2, 3}


def test_parse_changed_lines_ignores_non_file_diffs_and_deletions():
    diff_text = "\n".join(
        [
            "diff --git a/api/old.py b/api/old.py",
            "--- a/api/old.py",
            "+++ /dev/null",
            "@@ -1,2 +0,0 @@",
            "-print('a')",
            "-print('b')",
        ]
    )
    changed = parse_changed_lines_from_diff(diff_text)
    assert changed == {}


def test_parse_changed_lines_supports_hunk_without_count():
    diff_text = "\n".join(
        [
            "diff --git a/api/foo.py b/api/foo.py",
            "--- a/api/foo.py",
            "+++ b/api/foo.py",
            "@@ -1 +5 @@",
            "+print('x')",
        ]
    )
    changed = parse_changed_lines_from_diff(diff_text)
    assert changed["api/foo.py"] == {5}


def test_load_coverage_xml_ignores_incomplete_entries(tmp_path: Path):
    coverage_xml = "\n".join(
        [
            '<?xml version="1.0" ?>',
            "<coverage>",
            "  <packages>",
            '    <package name="api">',
            "      <classes>",
            '        <class name="no_filename">',
            "          <lines>",
            '            <line number="1" hits="1" />',
            "          </lines>",
            "        </class>",
            '        <class filename="api/no_lines.py">',
            "        </class>",
            '        <class filename="api/valid.py">',
            "          <lines>",
            '            <line hits="1" />',
            '            <line number="2" hits="1" />',
            "          </lines>",
            "        </class>",
            "      </classes>",
            "    </package>",
            "  </packages>",
            "</coverage>",
        ]
    )
    cov_path = _write_coverage_xml(tmp_path, coverage_xml)
    coverage_by_file = load_coverage_xml(cov_path)
    assert list(coverage_by_file.keys()) == ["api/valid.py"]
    assert coverage_by_file["api/valid.py"].covered_lines == {2}


def test_diff_coverage_percent_counts_missing_files_as_uncovered(tmp_path: Path):
    coverage_xml = "\n".join(
        [
            '<?xml version="1.0" ?>',
            '<coverage line-rate="1.0">',
            "  <packages>",
            '    <package name="api">',
            "      <classes>",
            '        <class filename="api/foo.py">',
            "          <lines>",
            '            <line number="1" hits="1" />',
            "          </lines>",
            "        </class>",
            "      </classes>",
            "    </package>",
            "  </packages>",
            "</coverage>",
        ]
    )
    cov_path = _write_coverage_xml(tmp_path, coverage_xml)
    coverage_by_file = load_coverage_xml(cov_path)

    covered, total, percent = diff_coverage_percent(
        coverage_by_file=coverage_by_file,
        changed_lines={"api/missing.py": {10, 11}},
    )
    assert (covered, total, percent) == (0, 2, 0.0)


def test_diff_coverage_percent_strips_apps_api_prefix(tmp_path: Path):
    coverage_xml = "\n".join(
        [
            '<?xml version="1.0" ?>',
            '<coverage line-rate="1.0">',
            "  <packages>",
            '    <package name="api">',
            "      <classes>",
            '        <class filename="api/foo.py">',
            "          <lines>",
            '            <line number="1" hits="1" />',
            "          </lines>",
            "        </class>",
            "      </classes>",
            "    </package>",
            "  </packages>",
            "</coverage>",
        ]
    )
    cov_path = _write_coverage_xml(tmp_path, coverage_xml)
    coverage_by_file = load_coverage_xml(cov_path)

    covered, total, percent = diff_coverage_percent(
        coverage_by_file=coverage_by_file,
        changed_lines={"apps/api/api/foo.py": {1}},
    )
    assert (covered, total, percent) == (1, 1, 100.0)


def test_critical_coverage_percent_applies_include_and_exclude(tmp_path: Path):
    coverage_xml = "\n".join(
        [
            '<?xml version="1.0" ?>',
            '<coverage line-rate="0.5">',
            "  <packages>",
            '    <package name="api">',
            "      <classes>",
            '        <class filename="api/a.py">',
            "          <lines>",
            '            <line number="1" hits="1" />',
            '            <line number="2" hits="0" />',
            "          </lines>",
            "        </class>",
            '        <class filename="api/b.py">',
            "          <lines>",
            '            <line number="1" hits="1" />',
            "          </lines>",
            "        </class>",
            "      </classes>",
            "    </package>",
            "  </packages>",
            "</coverage>",
        ]
    )
    cov_path = _write_coverage_xml(tmp_path, coverage_xml)
    coverage_by_file = load_coverage_xml(cov_path)

    covered, total, percent = critical_coverage_percent(
        coverage_by_file=coverage_by_file,
        include_globs=["api/*.py"],
        exclude_globs=["api/b.py"],
    )
    assert (covered, total, round(percent, 2)) == (1, 2, 50.0)


def test_main_diff_exits_nonzero_when_below_threshold(tmp_path: Path):
    coverage_xml = "\n".join(
        [
            '<?xml version="1.0" ?>',
            '<coverage line-rate="0.5">',
            "  <packages>",
            '    <package name="api">',
            "      <classes>",
            '        <class filename="api/foo.py">',
            "          <lines>",
            '            <line number="1" hits="1" />',
            '            <line number="2" hits="0" />',
            "          </lines>",
            "        </class>",
            "      </classes>",
            "    </package>",
            "  </packages>",
            "</coverage>",
        ]
    )
    cov_path = _write_coverage_xml(tmp_path, coverage_xml)

    diff_text = "\n".join(
        [
            "diff --git a/api/foo.py b/api/foo.py",
            "--- a/api/foo.py",
            "+++ b/api/foo.py",
            "@@ -0,0 +1,2 @@",
            "+print('a')",
            "+print('b')",
        ]
    )

    mock_run = MagicMock()
    mock_run.return_value.stdout = diff_text
    mock_run.return_value.returncode = 0

    with patch("scripts.ci.coverage_gate.subprocess.run", mock_run):
        rc = main(["diff", "--coverage-xml", str(cov_path), "--min-coverage", "60"])
    assert rc == 2


def test_main_diff_uses_base_ref_when_provided(tmp_path: Path):
    coverage_xml = "\n".join(
        [
            '<?xml version="1.0" ?>',
            "<coverage>",
            "  <packages>",
            '    <package name="api">',
            "      <classes>",
            '        <class filename="api/foo.py">',
            "          <lines>",
            '            <line number="1" hits="1" />',
            "          </lines>",
            "        </class>",
            "      </classes>",
            "    </package>",
            "  </packages>",
            "</coverage>",
        ]
    )
    cov_path = _write_coverage_xml(tmp_path, coverage_xml)

    diff_text = "\n".join(
        [
            "diff --git a/api/foo.py b/api/foo.py",
            "--- a/api/foo.py",
            "+++ b/api/foo.py",
            "@@ -0,0 +1,1 @@",
            "+print('a')",
        ]
    )

    mock_run = MagicMock()
    mock_run.return_value.stdout = diff_text
    mock_run.return_value.returncode = 0

    with patch("scripts.ci.coverage_gate.subprocess.run", mock_run):
        rc = main(
            [
                "diff",
                "--coverage-xml",
                str(cov_path),
                "--min-coverage",
                "90",
                "--base-ref",
                "origin/ver4",
            ]
        )
    assert rc == 0
    called_cmd = mock_run.call_args[0][0]
    assert "origin/ver4...HEAD" in called_cmd[-1]


def test_main_diff_uses_ci_fallback_when_github_actions_true(tmp_path: Path, monkeypatch):
    coverage_xml = "\n".join(
        [
            '<?xml version="1.0" ?>',
            "<coverage>",
            "  <packages>",
            '    <package name="api">',
            "      <classes>",
            '        <class filename="api/foo.py">',
            "          <lines>",
            '            <line number="1" hits="1" />',
            "          </lines>",
            "        </class>",
            "      </classes>",
            "    </package>",
            "  </packages>",
            "</coverage>",
        ]
    )
    cov_path = _write_coverage_xml(tmp_path, coverage_xml)

    diff_text = "\n".join(
        [
            "diff --git a/api/foo.py b/api/foo.py",
            "--- a/api/foo.py",
            "+++ b/api/foo.py",
            "@@ -0,0 +1,1 @@",
            "+print('a')",
        ]
    )

    mock_run = MagicMock()
    mock_run.return_value.stdout = diff_text
    mock_run.return_value.returncode = 0

    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    with patch("scripts.ci.coverage_gate.subprocess.run", mock_run):
        rc = main(["diff", "--coverage-xml", str(cov_path), "--min-coverage", "90"])
    assert rc == 0
    called_cmd = mock_run.call_args[0][0]
    assert called_cmd[-1] == "HEAD~1...HEAD"


def test_main_critical_exits_zero_when_threshold_met(tmp_path: Path):
    coverage_xml = "\n".join(
        [
            '<?xml version="1.0" ?>',
            '<coverage line-rate="1.0">',
            "  <packages>",
            '    <package name="api">',
            "      <classes>",
            '        <class filename="api/foo.py">',
            "          <lines>",
            '            <line number="1" hits="1" />',
            "          </lines>",
            "        </class>",
            "      </classes>",
            "    </package>",
            "  </packages>",
            "</coverage>",
        ]
    )
    cov_path = _write_coverage_xml(tmp_path, coverage_xml)

    rc = main(
        [
            "critical",
            "--coverage-xml",
            str(cov_path),
            "--include",
            "api/*.py",
            "--min-coverage",
            "90",
        ]
    )
    assert rc == 0


def test_main_critical_fails_when_empty_set(tmp_path: Path):
    cov_path = _write_coverage_xml(
        tmp_path,
        "\n".join(
            [
                '<?xml version="1.0" ?>',
                "<coverage>",
                "  <packages/>",
                "</coverage>",
            ]
        ),
    )
    rc = main(
        [
            "critical",
            "--coverage-xml",
            str(cov_path),
            "--include",
            "nope/*.py",
            "--min-coverage",
            "90",
        ]
    )
    assert rc == 2


def test_main_critical_fails_when_below_threshold(tmp_path: Path):
    coverage_xml = "\n".join(
        [
            '<?xml version="1.0" ?>',
            "<coverage>",
            "  <packages>",
            '    <package name="api">',
            "      <classes>",
            '        <class filename="api/foo.py">',
            "          <lines>",
            '            <line number="1" hits="0" />',
            "          </lines>",
            "        </class>",
            "      </classes>",
            "    </package>",
            "  </packages>",
            "</coverage>",
        ]
    )
    cov_path = _write_coverage_xml(tmp_path, coverage_xml)
    rc = main(
        [
            "critical",
            "--coverage-xml",
            str(cov_path),
            "--include",
            "api/*.py",
            "--min-coverage",
            "90",
        ]
    )
    assert rc == 2


def test_module_runs_as_script(tmp_path: Path, monkeypatch):
    coverage_xml = "\n".join(
        [
            '<?xml version="1.0" ?>',
            "<coverage>",
            "  <packages>",
            '    <package name="api">',
            "      <classes>",
            '        <class filename="api/foo.py">',
            "          <lines>",
            '            <line number="1" hits="1" />',
            "          </lines>",
            "        </class>",
            "      </classes>",
            "    </package>",
            "  </packages>",
            "</coverage>",
        ]
    )
    cov_path = _write_coverage_xml(tmp_path, coverage_xml)

    # Navigate from apps/api/tests/unit/ to repo root (4 levels up: unit -> tests -> api -> project root)
    module_path = Path(__file__).resolve().parents[4] / "scripts" / "ci" / "coverage_gate.py"
    monkeypatch.setenv("GITHUB_ACTIONS", "")
    monkeypatch.setattr(
        sys,
        "argv",
        ["coverage_gate.py", "critical", "--coverage-xml", str(cov_path), "--include", "api/*.py"],
    )
    with pytest.raises(SystemExit) as excinfo:
        runpy.run_path(str(module_path), run_name="__main__")
    assert excinfo.value.code == 0
