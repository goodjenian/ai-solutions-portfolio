#!/usr/bin/env python3
"""Run performance benchmarks for the AI Real Estate Assistant.

Usage:
    python scripts/run_performance_tests.py [--api] [--load] [--database] [--all]
"""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class BenchmarkResult:
    """Container for benchmark results."""

    name: str
    passed: bool
    duration: float
    details: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


def run_pytest(
    test_path: str,
    markers: list[str] | None = None,
    extra_args: list[str] | None = None,
) -> BenchmarkResult:
    """Run pytest and collect results."""
    start_time = time.time()

    cmd = ["pytest", test_path, "-v", "--tb=short", "-q"]

    if markers:
        cmd.extend(["-m", " and ".join(markers)])

    if extra_args:
        cmd.extend(extra_args)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent / "apps" / "api",
        )

        duration = time.time() - start_time
        passed = result.returncode == 0

        return BenchmarkResult(
            name=f"pytest: {test_path}",
            passed=passed,
            duration=duration,
            details={
                "returncode": result.returncode,
                "stdout": result.stdout[-1000:] if result.stdout else "",
                "stderr": result.stderr[-1000:] if result.stderr else "",
            },
            error=None if passed else result.stderr.split("\n")[-10:],
        )

    except Exception as e:
        return BenchmarkResult(
            name=f"pytest: {test_path}",
            passed=False,
            duration=time.time() - start_time,
            error=str(e),
        )


def run_lighthouse(
    url: str,
    config: str,
    output_path: str,
) -> BenchmarkResult:
    """Run Lighthouse audit."""
    start_time = time.time()

    cmd = [
        "npx",
        "lighthouse",
        url,
        f"--config-path={config}",
        f"--output-path={output_path}",
        "--output=json",
        "--output=html",
        "--chrome-flags=--headless",
        "--no-enable-error-reporting",
    ]

    try:
        _result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent / "apps" / "web",
        )

        duration = time.time() - start_time

        # Parse results
        scores = {}
        results_file = Path(output_path).with_suffix(".report.json")
        if results_file.exists():
            with open(results_file) as f:
                lh_result = json.load(f)
                categories = lh_result.get("categories", {})
                for cat_name, cat_data in categories.items():
                    scores[cat_name] = cat_data.get("score", 0) * 100

        passed = all(
            score >= 90
            for name, score in scores.items()
            if name in ["performance", "accessibility", "best-practices"]
        )

        return BenchmarkResult(
            name=f"Lighthouse: {url}",
            passed=passed,
            duration=duration,
            details={"scores": scores},
            error=None if passed else f"Scores below threshold: {scores}",
        )

    except Exception as e:
        return BenchmarkResult(
            name=f"Lighthouse: {url}",
            passed=False,
            duration=time.time() - start_time,
            error=str(e),
        )


def run_api_benchmarks() -> list[BenchmarkResult]:
    """Run API response time benchmarks."""
    results = []

    print("\n📊 Running API Response Time Benchmarks...")

    # Health endpoint
    result = run_pytest(
        "tests/performance/test_api_response_times.py",
        markers=["performance"],
        extra_args=["-k", "health"],
    )
    results.append(result)
    print(
        f"  {'✅' if result.passed else '❌'} Health endpoints: {result.duration:.1f}s"
    )

    # Search API (requires running server)
    if os.environ.get("RUN_INTEGRATION_TESTS"):
        result = run_pytest(
            "tests/performance/test_api_response_times.py",
            markers=["performance"],
            extra_args=["-k", "search"],
        )
        results.append(result)
        print(f"  {'✅' if result.passed else '❌'} Search API: {result.duration:.1f}s")

    return results


def run_load_tests() -> list[BenchmarkResult]:
    """Run load testing scenarios."""
    results = []

    print("\n📈 Running Load Tests...")

    if not os.environ.get("RUN_LOAD_TESTS"):
        print("  ⏭️  Skipping load tests (set RUN_LOAD_TESTS=1 to enable)")
        return results

    result = run_pytest(
        "tests/performance/test_load.py",
        markers=["load"],
    )
    results.append(result)
    print(f"  {'✅' if result.passed else '❌'} Load tests: {result.duration:.1f}s")

    return results


def run_database_benchmarks() -> list[BenchmarkResult]:
    """Run database performance tests."""
    results = []

    print("\n🗄️  Running Database Benchmarks...")

    if not os.environ.get("RUN_INTEGRATION_TESTS"):
        print("  ⏭️  Skipping database tests (set RUN_INTEGRATION_TESTS=1 to enable)")
        return results

    result = run_pytest(
        "tests/performance/test_database.py",
        markers=["database"],
    )
    results.append(result)
    print(f"  {'✅' if result.passed else '❌'} Database tests: {result.duration:.1f}s")

    return results


def run_lighthouse_audits() -> list[BenchmarkResult]:
    """Run Lighthouse performance audits."""
    results = []

    print("\n🔦 Running Lighthouse Audits...")

    web_dir = Path(__file__).parent.parent / "apps" / "web"
    output_dir = web_dir / ".lighthouseci"
    output_dir.mkdir(exist_ok=True)

    # Check if frontend is running
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")

    # Desktop audit
    result = run_lighthouse(
        url=frontend_url,
        config="lighthouse.config.js",
        output_path=str(output_dir / "desktop"),
    )
    results.append(result)

    if result.passed:
        print(f"  ✅ Desktop audit passed: {result.details.get('scores', {})}")
    else:
        print(f"  ❌ Desktop audit failed: {result.error}")

    # Mobile audit
    result = run_lighthouse(
        url=frontend_url,
        config="lighthouse.mobile.config.js",
        output_path=str(output_dir / "mobile"),
    )
    results.append(result)

    if result.passed:
        print(f"  ✅ Mobile audit passed: {result.details.get('scores', {})}")
    else:
        print(f"  ❌ Mobile audit failed: {result.error}")

    return results


def generate_report(results: list[BenchmarkResult]) -> str:
    """Generate a summary report."""
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.passed)
    total_duration = sum(r.duration for r in results)

    report = f"""
{"=" * 60}
Performance Benchmark Report
{"=" * 60}

Total Tests: {total_tests}
Passed: {passed_tests}
Failed: {total_tests - passed_tests}
Total Duration: {total_duration:.1f}s

Results:
"""

    for result in results:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        report += f"\n  {status} | {result.name} ({result.duration:.1f}s)"
        if result.error:
            report += f"\n         Error: {result.error[:100]}"

    report += f"\n\n{'=' * 60}"

    return report


def main():
    parser = argparse.ArgumentParser(description="Run performance benchmarks")
    parser.add_argument("--api", action="store_true", help="Run API benchmarks")
    parser.add_argument("--load", action="store_true", help="Run load tests")
    parser.add_argument(
        "--database", action="store_true", help="Run database benchmarks"
    )
    parser.add_argument(
        "--lighthouse", action="store_true", help="Run Lighthouse audits"
    )
    parser.add_argument("--all", action="store_true", help="Run all benchmarks")
    parser.add_argument("--report", type=str, help="Output file for report")

    args = parser.parse_args()

    # Default to --all if no specific option selected
    if not any([args.api, args.load, args.database, args.lighthouse]):
        args.all = True

    print("\n🚀 AI Real Estate Assistant - Performance Benchmarks")
    print("=" * 50)

    all_results = []

    if args.all or args.api:
        all_results.extend(run_api_benchmarks())

    if args.all or args.load:
        all_results.extend(run_load_tests())

    if args.all or args.database:
        all_results.extend(run_database_benchmarks())

    if args.all or args.lighthouse:
        all_results.extend(run_lighthouse_audits())

    # Generate report
    report = generate_report(all_results)
    print(report)

    # Save report if requested
    if args.report:
        with open(args.report, "w") as f:
            f.write(report)
        print(f"\n📄 Report saved to: {args.report}")

    # Exit with error if any tests failed
    if any(not r.passed for r in all_results):
        sys.exit(1)

    print("\n✨ All benchmarks passed!")
    sys.exit(0)


if __name__ == "__main__":
    main()
