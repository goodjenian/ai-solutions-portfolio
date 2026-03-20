"""
Unified Local Security Script (CI/CD Parity).

This script runs all security checks that are performed in CI/CD locally:
1. Gitleaks - Secret scanning (API keys, passwords, tokens)
2. Semgrep - SAST (Static Application Security Testing)
3. Bandit - Python code security analysis
4. pip-audit - Dependency vulnerability scanning

Mirrors the CI/CD security stage for local development and AI tool usage.

Usage:
    python scripts/security/local_scan.py              # Run all checks
    python scripts/security/local_scan.py --scan-only=secrets
    python scripts/security/local_scan.py --quick      # Skip slower checks

Exit codes:
    0 - All checks passed
    1 - One or more checks failed
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


class ScanStatus(str, Enum):
    """Scan result status."""

    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    WARNING = "WARNING"


@dataclass(frozen=True)
class ScanResult:
    """Result of a security scan."""

    name: str
    status: ScanStatus
    description: str
    details: str | None = None
    findings: list[str] | None = None

    def __post_init__(self):
        if self.findings is None:
            object.__setattr__(self, "findings", [])


class SecurityLocalRunner:
    """
    Unified local security runner.

    Runs CI/CD parity security checks with Docker fallbacks for Windows.
    """

    # Docker images for Windows fallback
    SEMGREP_IMAGE = "returntocorp/semgrep"
    GITLEAKS_IMAGE = "zricethezard/gitleaks"

    def __init__(self, root_dir: Path, verbose: bool = False):
        """
        Initialize the security runner.

        Args:
            root_dir: Root directory of the project
            verbose: Enable verbose output
        """
        self.root_dir = Path(root_dir).resolve()
        self.verbose = verbose
        self.is_windows = platform.system() == "Windows"
        self.results: list[ScanResult] = []

        # Verify we're in the project root
        if not (self.root_dir / ".gitleaks.toml").exists():
            raise FileNotFoundError(
                f"Expected to run from repository root (.gitleaks.toml not found at {self.root_dir})"
            )

    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"  [DEBUG] {message}", file=sys.stderr)

    def _run_command(
        self,
        cmd: list[str],
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> tuple[int, str, str]:
        """
        Run a command and return exit code, stdout, stderr.

        Args:
            cmd: Command to run
            cwd: Working directory (defaults to root_dir)
            env: Environment variables

        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        if cwd is None:
            cwd = self.root_dir

        self._log(f"Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            env={**os.environ, **(env or {})},
        )

        return result.returncode, result.stdout, result.stderr

    def _check_command_available(self, cmd: str) -> bool:
        """
        Check if a command is available on PATH.

        Args:
            cmd: Command name to check

        Returns:
            True if command is available
        """
        return shutil.which(cmd) is not None

    def _check_docker_available(self) -> bool:
        """Check if Docker is available."""
        return self._check_command_available("docker")

    def run_gitleaks(self) -> ScanResult:
        """
        Run Gitleaks secret scanning.

        Uses gitleaks binary if available, falls back to Docker on Windows.

        Returns:
            ScanResult with secrets findings
        """
        self._log("Running Gitleaks secret scanning...")

        cmd: list[str] = []
        use_docker = False

        # Try gitleaks binary first
        if self._check_command_available("gitleaks"):
            cmd = [
                "gitleaks",
                "detect",
                "--source",
                str(self.root_dir),
                "--config",
                ".gitleaks.toml",
            ]
        # Fall back to Docker
        elif self._check_docker_available():
            use_docker = True
            # Docker volume mount syntax differs by platform
            if self.is_windows:
                volume_mount = f"{self.root_dir}:/src"
            else:
                volume_mount = f"{self.root_dir}:/src"

            cmd = [
                "docker",
                "run",
                "--rm",
                "-v",
                volume_mount,
                self.GITLEAKS_IMAGE,
                "gitleaks",
                "detect",
                "--source",
                "/src",
                "--config",
                "/src/.gitleaks.toml",
            ]
        else:
            return ScanResult(
                name="Gitleaks (Secret Scanning)",
                status=ScanStatus.SKIPPED,
                description="Gitleaks not found. Install with: scoop install gitleaks (Windows) or brew install gitleaks (macOS)",
            )

        rc, stdout, stderr = self._run_command(cmd)

        findings: list[str] = []
        status = ScanStatus.PASSED

        # Gitleaks returns non-zero if leaks are found
        if rc != 0:
            # Parse output for findings
            output = stdout + stderr
            if "No leaks found" in output or "No leaks present" in output:
                status = ScanStatus.PASSED
            elif output:
                # Extract findings from JSON or text output
                findings.append(
                    f"Gitleaks detected potential secrets (exit code: {rc})"
                )
                if self.verbose:
                    findings.append(f"Output: {output[:500]}")
                status = ScanStatus.FAILED
            else:
                findings.append(f"Unexpected error (exit code: {rc})")
                status = ScanStatus.FAILED

        method = "Docker" if use_docker else "binary"
        return ScanResult(
            name="Gitleaks (Secret Scanning)",
            status=status,
            description=f"{'Secrets detected' if findings else 'No secrets found'} (via {method})",
            details=(stdout + stderr) if findings else None,
            findings=findings,
        )

    def run_semgrep(self) -> ScanResult:
        """
        Run Semgrep SAST scanning.

        Uses semgrep binary if available, falls back to Docker on Windows.

        Returns:
            ScanResult with SAST findings
        """
        self._log("Running Semgrep SAST scanning...")

        cmd: list[str] = []
        use_docker = False

        # Check for semgrep.yml config
        semgrep_config = self.root_dir / "semgrep.yml"
        if not semgrep_config.exists():
            return ScanResult(
                name="Semgrep (SAST)",
                status=ScanStatus.SKIPPED,
                description="semgrep.yml not found",
            )

        # Try semgrep binary first
        if self._check_command_available("semgrep"):
            cmd = [
                "semgrep",
                "--config",
                "auto",
                "--config",
                "semgrep.yml",
                "--error",
                "--severity",
                "ERROR",
                "--json",
            ]
        # Fall back to Docker
        elif self._check_docker_available():
            use_docker = True
            # Docker volume mount syntax differs by platform
            if self.is_windows:
                volume_mount = f"{self.root_dir}:/src"
            else:
                volume_mount = f"{self.root_dir}:/src"

            cmd = [
                "docker",
                "run",
                "--rm",
                "-v",
                volume_mount,
                self.SEMGREP_IMAGE,
                "semgrep",
                "--config",
                "auto",
                "--config",
                "/src/semgrep.yml",
                "--error",
                "--severity",
                "ERROR",
                "--json",
            ]
        else:
            return ScanResult(
                name="Semgrep (SAST)",
                status=ScanStatus.SKIPPED,
                description="Semgrep not found. Install with: pip install semgrep",
            )

        rc, stdout, stderr = self._run_command(cmd)

        findings: list[str] = []
        status = ScanStatus.PASSED

        # Semgrep returns non-zero if issues are found
        if rc != 0:
            # Parse JSON output
            try:
                # Try stdout first, then stderr
                json_output = stdout or stderr
                data = json.loads(json_output)
                results = data.get("results", [])

                for result in results:
                    findings.append(
                        f"{result.get('path', 'unknown')}:"
                        f"{result.get('start', {}).get('line', 0)}: "
                        f"{result.get('message', 'no message')}"
                    )

                status = ScanStatus.FAILED if findings else ScanStatus.PASSED
            except json.JSONDecodeError:
                # Not JSON output, use text parsing
                output = stdout + stderr
                if output:
                    findings.append(f"Semgrep detected issues (exit code: {rc})")
                    if self.verbose:
                        findings.append(f"Output: {output[:500]}")
                    status = ScanStatus.FAILED

        method = "Docker" if use_docker else "binary"
        return ScanResult(
            name="Semgrep (SAST)",
            status=status,
            description=f"{'Issues detected' if findings else 'No issues found'} (via {method})",
            details=(stdout + stderr) if findings else None,
            findings=findings,
        )

    def run_bandit(self) -> ScanResult:
        """
        Run Bandit Python security scanning.

        Returns:
            ScanResult with security findings
        """
        self._log("Running Bandit security scanning...")

        # Check if bandit is installed
        rc, _, _ = self._run_command([sys.executable, "-m", "pip", "show", "bandit"])
        if rc != 0:
            return ScanResult(
                name="Bandit (Python Security)",
                status=ScanStatus.SKIPPED,
                description="Bandit not installed. Install with: uv pip install bandit",
            )

        # Target directories (matching CI configuration)
        targets = [
            "api",
            "agents",
            "ai",
            "analytics",
            "config",
            "data",
            "models",
            "notifications",
            "rules",
            "tools",
            "utils",
            "vector_store",
            "workflows",
        ]
        existing_targets = [t for t in targets if (self.root_dir / t).exists()]

        if not existing_targets:
            return ScanResult(
                name="Bandit (Python Security)",
                status=ScanStatus.SKIPPED,
                description="No target directories found",
            )

        cmd = [
            sys.executable,
            "-m",
            "bandit",
            "-r",
            *existing_targets,
            "-f",
            "json",
            "-lll",
            "-iii",
        ]

        # Exclude scripts/ci (matches CI)
        if (self.root_dir / "scripts" / "ci").exists():
            cmd.extend(["-x", "scripts/ci"])

        rc, stdout, stderr = self._run_command(cmd)

        findings: list[str] = []
        status = ScanStatus.PASSED

        if rc != 0:
            try:
                bandit_data = json.loads(stdout)
                for result in bandit_data.get("results", []):
                    findings.append(
                        f"{result.get('filename', 'unknown')}:"
                        f"{result.get('line_number', 0)}: "
                        f"{result.get('issue_text', 'no description')} "
                        f"({result.get('issue_severity', 'UNKNOWN')} severity)"
                    )
                status = ScanStatus.FAILED
            except json.JSONDecodeError:
                findings.append(f"Failed to parse Bandit output: {stdout[:200]}")
                status = ScanStatus.FAILED

        return ScanResult(
            name="Bandit (Python Security)",
            status=status,
            description=f"{'Issues detected' if findings else 'No issues found'}",
            details=stdout if findings else None,
            findings=findings,
        )

    def run_pip_audit(self) -> ScanResult:
        """
        Run pip-audit dependency vulnerability scanning.

        Returns:
            ScanResult with vulnerability findings
        """
        self._log("Running pip-audit dependency scanning...")

        # Check if pip-audit is installed
        rc, _, _ = self._run_command([sys.executable, "-m", "pip", "show", "pip-audit"])
        if rc != 0:
            return ScanResult(
                name="pip-audit (Dependency Scan)",
                status=ScanStatus.SKIPPED,
                description="pip-audit not installed. Install with: uv pip install pip-audit",
            )

        requirements_file = self.root_dir / "requirements.txt"
        if not requirements_file.exists():
            return ScanResult(
                name="pip-audit (Dependency Scan)",
                status=ScanStatus.SKIPPED,
                description="requirements.txt not found",
            )

        cmd = [
            sys.executable,
            "-m",
            "pip_audit",
            "-r",
            str(requirements_file),
            "--format",
            "json",
            "--ignore-vuln",
            "GHSA-7gcm-g887-7qv7",
            "--ignore-vuln",
            "CVE-2026-0994",
        ]

        rc, stdout, stderr = self._run_command(cmd)

        findings: list[str] = []
        status = ScanStatus.PASSED

        if rc != 0:
            try:
                vuln_data = json.loads(stdout)
                for vuln in vuln_data.get("vulnerabilities", []):
                    findings.append(
                        f"{vuln.get('name', 'unknown')}: "
                        f"{vuln.get('description', 'no description')}"
                    )
                status = ScanStatus.FAILED
            except json.JSONDecodeError:
                findings.append(f"Failed to parse pip-audit output: {stdout[:200]}")
                status = ScanStatus.FAILED

        return ScanResult(
            name="pip-audit (Dependency Scan)",
            status=status,
            description=f"{'Vulnerabilities detected' if findings else 'No vulnerabilities found'}",
            details=stdout if findings else None,
            findings=findings,
        )

    def run_all(
        self,
        *,
        scan_only: str | None = None,
        quick: bool = False,
    ) -> list[ScanResult]:
        """
        Run security scans.

        Args:
            scan_only: Run only specific scan (secrets, semgrep, bandit, pip-audit)
            quick: Skip slower checks (pip-audit)

        Returns:
            List of ScanResult objects
        """
        print("Running local security scans (CI/CD parity)...")
        print()

        if scan_only:
            scan_map = {
                "secrets": self.run_gitleaks,
                "semgrep": self.run_semgrep,
                "bandit": self.run_bandit,
                "pip-audit": self.run_pip_audit,
                "sast": self.run_semgrep,  # Alias
                "deps": self.run_pip_audit,  # Alias
            }

            scanner = scan_map.get(scan_only.lower())
            if scanner is None:
                print(f"Unknown scan type: {scan_only}")
                print(f"Available: {', '.join(scan_map.keys())}")
                raise SystemExit(1)

            self.results = [scanner()]
        else:
            # Run all scans (order matches CI: gitleaks, semgrep, bandit, pip-audit)
            self.results = [
                self.run_gitleaks(),
                self.run_semgrep(),
                self.run_bandit(),
            ]

            # Skip pip-audit in quick mode
            if not quick:
                self.results.append(self.run_pip_audit())
            else:
                print("(Quick mode: skipping pip-audit dependency scan)")

        return self.results

    def print_report(self) -> None:
        """Print security scan report."""
        print()
        print("=" * 70)
        print("LOCAL SECURITY SCAN REPORT (CI/CD Parity)")
        print("=" * 70)
        print()

        failed_count = 0
        warning_count = 0
        skipped_count = 0

        for result in self.results:
            status_symbol = {
                ScanStatus.PASSED: "\u2713",  # ✓
                ScanStatus.FAILED: "\u2717",  # ✗
                ScanStatus.SKIPPED: "\u2298",  # ⊘
                ScanStatus.WARNING: "\u26a0",  # ⚠
            }.get(result.status, "?")

            # Use ANSI colors on supported terminals
            status_color = {
                ScanStatus.PASSED: "\033[92m",  # Green
                ScanStatus.FAILED: "\033[91m",  # Red
                ScanStatus.SKIPPED: "\033[93m",  # Yellow
                ScanStatus.WARNING: "\033[93m",  # Yellow
            }.get(result.status, "")

            reset_color = "\033[0m"

            # Print status with color if supported, otherwise plain text
            try:
                print(
                    f"{status_color}{status_symbol}{reset_color} {result.name}: {result.status.value}"
                )
            except Exception:
                # Fallback for Windows cmd without ANSI support
                print(f"[{result.status.value}] {result.name}")

            print(f"  {result.description}")

            if result.findings:
                limit = 10
                print(f"  Findings ({len(result.findings)}):")
                for finding in result.findings[:limit]:
                    print(f"    - {finding}")
                if len(result.findings) > limit:
                    print(f"    ... and {len(result.findings) - limit} more")

            print()

            if result.status == ScanStatus.FAILED:
                failed_count += 1
            elif result.status == ScanStatus.WARNING:
                warning_count += 1
            elif result.status == ScanStatus.SKIPPED:
                skipped_count += 1

        print("=" * 70)
        print(
            f"Summary: {failed_count} failed, {warning_count} warnings, "
            f"{skipped_count} skipped, "
            f"{len(self.results) - failed_count - warning_count - skipped_count} passed"
        )
        print("=" * 70)

    def get_exit_code(self) -> int:
        """
        Get exit code based on scan results.

        Returns:
            1 if any checks failed, 0 otherwise
        """
        return 1 if any(r.status == ScanStatus.FAILED for r in self.results) else 0


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run CI/CD parity security scans locally",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              Run all security scans
  %(prog)s --scan-only=secrets           Run only Gitleaks secret scanning
  %(prog)s --scan-only=semgrep           Run only Semgrep SAST
  %(prog)s --quick                       Skip slower checks (pip-audit)
  %(prog)s --verbose                     Enable verbose output

Available scans:
  secrets    Gitleaks secret scanning
  semgrep    Semgrep SAST (alias: sast)
  bandit     Bandit Python security
  pip-audit  Dependency scanning (alias: deps)
        """,
    )
    parser.add_argument(
        "--root-dir",
        type=Path,
        default=Path.cwd(),
        help="Root directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--scan-only",
        choices=["secrets", "semgrep", "bandit", "pip-audit", "sast", "deps"],
        help="Run only specific scan",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Skip slower checks (pip-audit)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    """Main entry point."""
    args = parse_args(argv)

    runner = SecurityLocalRunner(root_dir=args.root_dir, verbose=args.verbose)

    try:
        runner.run_all(scan_only=args.scan_only, quick=args.quick)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    runner.print_report()
    return runner.get_exit_code()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
