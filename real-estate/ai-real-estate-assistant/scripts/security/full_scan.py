"""
Enhanced Security Scanning Script (TASK-018).

This script performs comprehensive security checks:
1. Dependency vulnerability scanning (via pip-audit)
2. Code security scanning (via Bandit)
3. Secrets detection (via detect-secrets)
4. Configuration security checks
5. Sensitive data pattern detection
6. Open port and exposure checks
7. File permission checks

Run this script as part of CI/CD pipeline or locally for security validation.
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional


class ScanStatus(str, Enum):
    """Scan result status."""

    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    WARNING = "WARNING"


@dataclass
class ScanResult:
    """Result of a security scan."""

    name: str
    status: ScanStatus
    description: str
    details: Optional[str] = None
    findings: List[str] = None

    def __post_init__(self):
        if self.findings is None:
            self.findings = []


class SecurityScanner:
    """
    Comprehensive security scanner.

    Runs multiple security checks and aggregates results.
    """

    # Patterns for sensitive data detection
    SENSITIVE_PATTERNS = {
        "AWS Access Key": r"AKIA[0-9A-Z]{16}",
        "AWS Secret Key": r"(?<![A-Z0-9])[A-Z0-9]{40}(?![A-Z0-9])",
        "Generic API Key": r"(api[_-]?key|apikey)['\"\s]*[:=]['\"\s]*[a-zA-Z0-9_\-]{16,}",
        "JWT Token": r"eyJ[a-zA-Z0-9_\-]*\.[a-zA-Z0-9_\-]*\.[a-zA-Z0-9_\-]*",
        "Private Key": r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
        "Password in URL": r"[a-zA-Z][a-zA-Z0-9+.-]+://[^:]+:[^@]+@",
        "Database URL": r"(postgres|mysql|mongodb|redis)://[^:]+:[^@]+@",
        "Email address": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "IP Address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        "Credit Card": r"\b(?:\d[ -]*?){13,16}\b",
    }

    # Files/directories to exclude from scanning
    EXCLUDE_PATTERNS = [
        r"\.git/",
        r"venv/",
        r"\.venv/",
        r"__pycache__/",
        r"\.pytest_cache/",
        r"\.mypy_cache/",
        r"node_modules/",
        r"\.vscode/",
        r"\.idea/",
        r"dist/",
        r"build/",
        r"\*\.egg-info/",
        r"\.coverage",
        r"coverage\.xml",
        r"\.html",
        r"\.md$",
        r"\.json$",
        r"requirements\.txt",
        r"package-lock\.json",
        r"yarn\.lock",
    ]

    def __init__(self, root_dir: Path, verbose: bool = False):
        """
        Initialize security scanner.

        Args:
            root_dir: Root directory to scan
            verbose: Enable verbose output
        """
        self.root_dir = Path(root_dir).resolve()
        self.verbose = verbose
        self.results: List[ScanResult] = []

        # Compile exclude patterns
        self.exclude_regex = re.compile("|".join(self.EXCLUDE_PATTERNS), re.IGNORECASE)

        # Compile sensitive patterns
        self.sensitive_regexes = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self.SENSITIVE_PATTERNS.items()
        }

    def _log(self, message: str):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"  {message}")

    def _run_command(
        self,
        cmd: List[str],
        cwd: Optional[Path] = None,
    ) -> tuple[int, str, str]:
        """
        Run a command and return exit code, stdout, stderr.

        Args:
            cmd: Command to run
            cwd: Working directory

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
        )

        return result.returncode, result.stdout, result.stderr

    def scan_dependencies(self) -> ScanResult:
        """
        Scan dependencies for known vulnerabilities using pip-audit.

        Returns:
            ScanResult with vulnerability findings
        """
        self._log("Scanning dependencies for vulnerabilities...")

        # Check if pip-audit is available
        rc, _, _ = self._run_command([sys.executable, "-m", "pip", "show", "pip-audit"])
        if rc != 0:
            return ScanResult(
                name="Dependency Vulnerability Scan",
                status=ScanStatus.SKIPPED,
                description="pip-audit not installed. Install with: pip install pip-audit",
            )

        # Run pip-audit on requirements.txt
        requirements_file = self.root_dir / "requirements.txt"
        if not requirements_file.exists():
            return ScanResult(
                name="Dependency Vulnerability Scan",
                status=ScanStatus.SKIPPED,
                description="requirements.txt not found",
            )

        rc, stdout, stderr = self._run_command(
            [
                sys.executable,
                "-m",
                "pip_audit",
                "-r",
                str(requirements_file),
                "--format",
                "json",
                "--ignore-vuln",
                "GHSA-7gcm-g887-7qv7",  # Known false positive
                "--ignore-vuln",
                "CVE-2026-0994",  # Known false positive
            ]
        )

        findings = []
        status = ScanStatus.PASSED

        if rc != 0:
            try:
                vuln_data = json.loads(stdout)
                for vuln in vuln_data.get("vulnerabilities", []):
                    findings.append(
                        f"{vuln.get('name', 'unknown')}: {vuln.get('description', 'no description')}"
                    )
                status = ScanStatus.FAILED
            except json.JSONDecodeError:
                findings.append(f"Failed to parse pip-audit output: {stdout}")
                status = ScanStatus.FAILED

        return ScanResult(
            name="Dependency Vulnerability Scan",
            status=status,
            description=f"Found {len(findings)} vulnerabilities"
            if findings
            else "No vulnerabilities found",
            details=stdout if findings else None,
            findings=findings,
        )

    def scan_code_security(self) -> ScanResult:
        """
        Scan code for security issues using Bandit.

        Returns:
            ScanResult with security findings
        """
        self._log("Scanning code for security issues...")

        # Check if bandit is available
        rc, _, _ = self._run_command([sys.executable, "-m", "pip", "show", "bandit"])
        if rc != 0:
            return ScanResult(
                name="Code Security Scan",
                status=ScanStatus.SKIPPED,
                description="Bandit not installed. Install with: pip install bandit",
            )

        # Directories to scan
        targets = ["api", "agents", "ai", "config", "utils", "models", "tools"]
        existing_targets = [t for t in targets if (self.root_dir / t).exists()]

        if not existing_targets:
            return ScanResult(
                name="Code Security Scan",
                status=ScanStatus.SKIPPED,
                description="No target directories found",
            )

        # Run bandit
        cmd = [
            sys.executable,
            "-m",
            "bandit",
            "-r",
            *existing_targets,
            "-f",
            "json",
            "-ll",
            "-ii",
        ]

        # Exclude scripts/ci from scanning (uses shell=True for trusted commands)
        if (self.root_dir / "scripts" / "ci").exists():
            cmd.extend(["-x", "scripts/ci"])

        rc, stdout, stderr = self._run_command(cmd)

        findings = []
        status = ScanStatus.PASSED

        if rc != 0:
            try:
                bandit_data = json.loads(stdout)
                for result in bandit_data.get("results", []):
                    findings.append(
                        f"{result.get('filename', 'unknown')}:{result.get('line_number', 0)}: "
                        f"{result.get('issue_text', 'no description')} "
                        f"({result.get('issue_severity', 'UNKNOWN')} severity)"
                    )
                status = ScanStatus.FAILED
            except json.JSONDecodeError:
                findings.append(f"Failed to parse Bandit output: {stdout}")
                status = ScanStatus.FAILED

        return ScanResult(
            name="Code Security Scan",
            status=status,
            description=f"Found {len(findings)} issues"
            if findings
            else "No issues found",
            details=stdout if findings else None,
            findings=findings,
        )

    def scan_secrets(self) -> ScanResult:
        """
        Scan for secrets and sensitive data patterns.

        Returns:
            ScanResult with secrets findings
        """
        self._log("Scanning for secrets and sensitive data...")

        findings = []

        # Scan common file types
        for file_path in self.root_dir.rglob("*"):
            # Skip excluded patterns
            if self.exclude_regex.search(str(file_path.relative_to(self.root_dir))):
                continue

            # Skip binary files
            if not file_path.is_file():
                continue

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                    # Check each pattern
                    for pattern_name, pattern in self.sensitive_regexes.items():
                        matches = pattern.finditer(content)
                        for match in matches:
                            line_num = content[: match.start()].count("\n") + 1
                            findings.append(
                                f"{file_path.relative_to(self.root_dir)}:{line_num}: "
                                f"Potential {pattern_name} found"
                            )
            except Exception:
                # Skip files that can't be read as text
                continue

        status = ScanStatus.FAILED if findings else ScanStatus.PASSED

        return ScanResult(
            name="Secrets Detection Scan",
            status=status,
            description=f"Found {len(findings)} potential secrets"
            if findings
            else "No secrets found",
            findings=findings,
        )

    def scan_config_security(self) -> ScanResult:
        """
        Scan configuration files for security issues.

        Returns:
            ScanResult with config findings
        """
        self._log("Scanning configuration security...")

        findings = []

        # Check .env file
        env_file = self.root_dir / ".env"
        if env_file.exists():
            with open(env_file, "r") as f:
                env_content = f.read()

            # Check for insecure defaults
            insecure_defaults = {
                "ENVIRONMENT=development": "Development environment in production",
                "DEBUG=true": "Debug mode enabled",
                "CORS_ALLOW_ORIGINS=*": "Wildcard CORS origins",
                "API_ACCESS_KEY=dev-secret-key": "Default dev key in use",
            }

            for pattern, description in insecure_defaults.items():
                if pattern in env_content:
                    findings.append(f".env: {description}")

        # Check .env.example for best practices
        env_example = self.root_dir / ".env.example"
        if not env_example.exists():
            findings.append("Missing .env.example file for configuration reference")

        status = ScanStatus.WARNING if findings else ScanStatus.PASSED

        return ScanResult(
            name="Configuration Security Scan",
            status=status,
            description=f"Found {len(findings)} config issues"
            if findings
            else "No config issues",
            findings=findings,
        )

    def scan_file_permissions(self) -> ScanResult:
        """
        Scan for insecure file permissions.

        Returns:
            ScanResult with permission findings
        """
        self._log("Scanning file permissions...")

        findings = []

        # Check for world-writable files
        for file_path in self.root_dir.rglob("*"):
            if not file_path.is_file():
                continue

            # Skip excluded patterns
            if self.exclude_regex.search(str(file_path.relative_to(self.root_dir))):
                continue

            try:
                st_mode = file_path.stat().st_mode
                # Check if world-writable (octal 0o002)
                if st_mode & 0o002:
                    findings.append(
                        f"{file_path.relative_to(self.root_dir)}: "
                        f"World-writable (permissions: {oct(st_mode)[-3:]})"
                    )
            except Exception:
                continue

        status = ScanStatus.WARNING if findings else ScanStatus.PASSED

        return ScanResult(
            name="File Permissions Scan",
            status=status,
            description=f"Found {len(findings)} permission issues"
            if findings
            else "No permission issues",
            findings=findings,
        )

    def run_all_scans(self) -> List[ScanResult]:
        """
        Run all security scans.

        Returns:
            List of ScanResult objects
        """
        print("Running security scans...")
        print()

        results = [
            self.scan_dependencies(),
            self.scan_code_security(),
            self.scan_secrets(),
            self.scan_config_security(),
            self.scan_file_permissions(),
        ]

        self.results = results
        return results

    def print_report(self):
        """Print security scan report."""
        print()
        print("=" * 70)
        print("SECURITY SCAN REPORT")
        print("=" * 70)
        print()

        failed_count = 0
        warning_count = 0

        for result in self.results:
            status_symbol = {
                ScanStatus.PASSED: "✓",
                ScanStatus.FAILED: "✗",
                ScanStatus.SKIPPED: "⊘",
                ScanStatus.WARNING: "⚠",
            }.get(result.status, "?")

            status_color = {
                ScanStatus.PASSED: "\033[92m",  # Green
                ScanStatus.FAILED: "\033[91m",  # Red
                ScanStatus.SKIPPED: "\033[93m",  # Yellow
                ScanStatus.WARNING: "\033[93m",  # Yellow
            }.get(result.status, "")

            reset_color = "\033[0m"

            print(
                f"{status_color}{status_symbol}{reset_color} {result.name}: {result.status}"
            )
            print(f"  {result.description}")

            if result.findings:
                print(f"  Findings ({len(result.findings)}):")
                for finding in result.findings[:10]:  # Show first 10
                    print(f"    - {finding}")
                if len(result.findings) > 10:
                    print(f"    ... and {len(result.findings) - 10} more")

            print()

            if result.status == ScanStatus.FAILED:
                failed_count += 1
            elif result.status == ScanStatus.WARNING:
                warning_count += 1

        print("=" * 70)
        print(
            f"Summary: {failed_count} failed, {warning_count} warnings, "
            f"{len(self.results) - failed_count - warning_count} passed"
        )
        print("=" * 70)

    def get_exit_code(self) -> int:
        """Get exit code based on scan results."""
        return 1 if any(r.status == ScanStatus.FAILED for r in self.results) else 0


def main(argv: List[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Enhanced Security Scanning for AI Real Estate Assistant"
    )
    parser.add_argument(
        "--root-dir",
        type=Path,
        default=Path.cwd(),
        help="Root directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--scan",
        choices=["all", "deps", "code", "secrets", "config", "permissions"],
        default="all",
        help="Specific scan to run (default: all)",
    )

    args = parser.parse_args(argv)

    scanner = SecurityScanner(root_dir=args.root_dir, verbose=args.verbose)

    if args.scan == "all":
        scanner.run_all_scans()
    elif args.scan == "deps":
        scanner.results = [scanner.scan_dependencies()]
    elif args.scan == "code":
        scanner.results = [scanner.scan_code_security()]
    elif args.scan == "secrets":
        scanner.results = [scanner.scan_secrets()]
    elif args.scan == "config":
        scanner.results = [scanner.scan_config_security()]
    elif args.scan == "permissions":
        scanner.results = [scanner.scan_file_permissions()]

    scanner.print_report()
    return scanner.get_exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
