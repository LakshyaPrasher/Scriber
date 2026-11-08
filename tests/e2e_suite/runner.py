"""Scriber E2E Test Suite Unified CLI Runner.

Executes and reports on the 4-tier requirement-driven E2E test suite:
- Tier 1: Feature Coverage (F1 to F20)
- Tier 2: Boundary & Corner Cases (F1 to F20)
- Tier 3: Cross-Feature Pairwise Interactions
- Tier 4: Real-World Multi-Speaker Application Scenarios

Usage:
    python tests/e2e_suite/runner.py --tier 1
    python tests/e2e_suite/runner.py --tier 2
    python tests/e2e_suite/runner.py --tier 3
    python tests/e2e_suite/runner.py --tier 4
    python tests/e2e_suite/runner.py --all
    python tests/e2e_suite/runner.py --json-summary report.json
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time
import unittest
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

TIER_MODULE_MAP = {
    1: "tests.e2e_suite.test_tier1_features",
    2: "tests.e2e_suite.test_tier2_boundaries",
    3: "tests.e2e_suite.test_tier3_pairwise",
    4: "tests.e2e_suite.test_tier4_scenarios",
}



def build_suite_for_tiers(tiers: List[int]) -> unittest.TestSuite:
    """Builds a composite test suite for specified tiers."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for tier_num in tiers:
        module_name = TIER_MODULE_MAP.get(tier_num)
        if not module_name:
            continue
        try:
            mod_suite = loader.loadTestsFromName(module_name)
            suite.addTests(mod_suite)
        except Exception as e:
            print(f"[-] Warning: Failed to load tests from {module_name}: {e}", file=sys.stderr)

    return suite


def run_e2e_suite(
    tiers: List[int],
    verbosity: int = 2,
    json_summary_path: Optional[str] = None,
) -> bool:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 72)
    print("SCRIBER E2E TEST SUITE RUNNER")
    print(f"Executing Tiers: {', '.join(str(t) for t in tiers)}")
    print("=" * 72)

    start_time = time.time()
    suite = build_suite_for_tiers(tiers)
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    elapsed = time.time() - start_time

    total_tests = result.testsRun
    failures_count = len(result.failures)
    errors_count = len(result.errors)
    skipped_count = len(result.skipped)
    passed_count = total_tests - (failures_count + errors_count + skipped_count)

    success = (failures_count == 0 and errors_count == 0)

    print("\n" + "=" * 72)
    print("E2E EXECUTION SUMMARY")
    print("=" * 72)
    print(f"  Total Tests Executed: {total_tests}")
    print(f"  Passed:               {passed_count}  ({(passed_count / max(1, total_tests))*100:.1f}%)")
    print(f"  Skipped (milestone):  {skipped_count}")
    print(f"  Failures:             {failures_count}")
    print(f"  Errors:               {errors_count}")
    print(f"  Execution Time:       {elapsed:.2f} seconds")
    print(f"  Overall Status:       {'[PASSED]' if success else '[FAILED]'}")
    print("=" * 72)


    if json_summary_path:
        summary_data = {
            "tiers_executed": tiers,
            "total_tests": total_tests,
            "passed": passed_count,
            "skipped": skipped_count,
            "failures": failures_count,
            "errors": errors_count,
            "elapsed_seconds": round(elapsed, 2),
            "success": success,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        with open(json_summary_path, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2)
        print(f"[*] JSON summary written to: {json_summary_path}")

    return success


def main() -> None:
    parser = argparse.ArgumentParser(description="Scriber E2E Test Suite Runner")
    parser.add_argument(
        "--tier",
        type=int,
        choices=[1, 2, 3, 4],
        help="Run a specific tier (1, 2, 3, or 4)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all 4 tiers (Tiers 1, 2, 3, and 4)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_const",
        dest="verbosity",
        const=2,
        default=2,
        help="Verbose output",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_const",
        dest="verbosity",
        const=1,
        help="Quiet output",
    )
    parser.add_argument(
        "--json-summary",
        type=str,
        default=None,
        help="Path to output JSON summary report",
    )

    args = parser.parse_args()

    if args.tier:
        tiers_to_run = [args.tier]
    else:
        tiers_to_run = [1, 2, 3, 4]

    success = run_e2e_suite(
        tiers=tiers_to_run,
        verbosity=args.verbosity,
        json_summary_path=args.json_summary,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
