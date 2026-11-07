#!/usr/bin/env python3
r"""
Backend automated test runner for Whicoustic platform.
Executes test suites directly on D:\ without requiring third-party test runners on C:\.
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import os
import sys
import time
import traceback
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


def run_test_module(module_name: str) -> tuple[int, int, list[str]]:
    """Run all test_* functions and unittest.TestCase classes in a module.

    Returns (passed_count, failed_count, failure_details).
    """
    passed = 0
    failed = 0
    failures: list[str] = []

    try:
        mod = importlib.import_module(module_name)
    except Exception as exc:
        failures.append(f"Failed to import {module_name}: {exc}\n{traceback.format_exc()}")
        return 0, 1, failures

    # 1. Discover standalone test functions
    test_functions = []
    for attr_name in dir(mod):
        if attr_name.startswith("test_"):
            attr = getattr(mod, attr_name)
            if inspect.isfunction(attr):
                test_functions.append((attr_name, attr))

    # 2. Discover unittest.TestCase subclasses
    test_case_classes = []
    for attr_name in dir(mod):
        attr = getattr(mod, attr_name)
        if inspect.isclass(attr) and issubclass(attr, unittest.TestCase):
            test_case_classes.append(attr)

    print(f"\n--- Running module: {module_name} ---")

    # Run standalone test functions
    for name, fn in test_functions:
        t0 = time.perf_counter()
        try:
            fn()
            dt = (time.perf_counter() - t0) * 1000
            print(f"  [PASS] {name} ({dt:.1f}ms)")
            passed += 1
        except Exception as exc:
            dt = (time.perf_counter() - t0) * 1000
            print(f"  [FAIL] {name} ({dt:.1f}ms): {exc}")
            failed += 1
            failures.append(f"{module_name}.{name}: {exc}\n{traceback.format_exc()}")

    # Run TestCase classes if any
    for test_class in test_case_classes:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(test_class)
        result = unittest.TestResult()
        t0 = time.perf_counter()
        suite.run(result)
        dt = (time.perf_counter() - t0) * 1000
        class_name = test_class.__name__
        if result.wasSuccessful():
            print(f"  [PASS] {class_name} ({suite.countTestCases()} tests) ({dt:.1f}ms)")
            passed += suite.countTestCases()
        else:
            print(f"  [FAIL] {class_name} ({suite.countTestCases()} tests)")
            failed += len(result.failures) + len(result.errors)
            for test, err in result.failures + result.errors:
                failures.append(f"{class_name}.{test}: {err}")

    return passed, failed, failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Whicoustic Backend Test Runner")
    parser.add_argument(
        "modules",
        nargs="*",
        default=["tests.test_user_sync"],
        help="Test modules to run (e.g. tests.test_user_sync)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Whicoustic Backend Test Suite")
    print(f"Working directory: {BASE_DIR}")
    print(f"Backend directory: {BACKEND_DIR}")
    print(f"Target modules: {args.modules}")
    print("=" * 60)

    total_passed = 0
    total_failed = 0
    all_failures: list[str] = []

    start_time = time.perf_counter()
    for mod in args.modules:
        passed, failed, failures = run_test_module(mod)
        total_passed += passed
        total_failed += failed
        all_failures.extend(failures)

    total_duration = time.perf_counter() - start_time

    print("\n" + "=" * 60)
    print(f"Test Run Summary:")
    print(f"  Total tests executed: {total_passed + total_failed}")
    print(f"  Passed: {total_passed}")
    print(f"  Failed: {total_failed}")
    print(f"  Total time: {total_duration:.2f}s")
    print("=" * 60)

    if all_failures:
        print("\nFailures:")
        for fail in all_failures:
            print(fail)
            print("-" * 40)
        return 1

    print("\nALL BACKEND TESTS PASSED (100%)!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
