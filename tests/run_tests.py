#!/usr/bin/env python3
"""
Test runner for the Decaf compiler (dcc).

Usage:
    python run_tests.py <tests_dir>

For each .decaf file under <tests_dir>:
  - Files named bad*.decaf are expected to produce compiler errors (non-zero exit).
  - All other files are expected to compile successfully (zero exit).

The path to the dcc executable is read from the DCC environment variable.
"""

import os
import sys
import subprocess
import glob


def find_decaf_files(tests_dir):
    """Recursively find all .decaf files under tests_dir."""
    files = []
    for root, _, filenames in os.walk(tests_dir):
        for f in filenames:
            if f.endswith(".decaf"):
                files.append(os.path.join(root, f))
    files.sort()
    return files


def is_expected_to_fail(filepath):
    """Files named bad*.decaf are expected to produce errors."""
    basename = os.path.basename(filepath)
    return basename.startswith("bad")


def run_test(dcc_path, decaf_file, expect_error):
    """Run dcc on a decaf file and check the result."""
    try:
        with open(decaf_file, "r") as f:
            result = subprocess.run(
                [dcc_path],
                stdin=f,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
            )
        success = (result.returncode != 0) if expect_error else (result.returncode == 0)
        return success, result.returncode, result.stderr.decode("utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return False, -1, "TIMEOUT"
    except Exception as e:
        return False, -1, str(e)


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_tests.py <tests_dir>")
        sys.exit(1)

    tests_dir = sys.argv[1]
    dcc_path = os.environ.get("DCC", "")

    if not dcc_path:
        print("ERROR: DCC environment variable not set!")
        sys.exit(1)

    if not os.path.isfile(dcc_path):
        print(f"ERROR: dcc executable not found at: {dcc_path}")
        sys.exit(1)

    if not os.path.isdir(tests_dir):
        print(f"ERROR: tests directory not found: {tests_dir}")
        sys.exit(1)

    files = find_decaf_files(tests_dir)
    if not files:
        print("No .decaf test files found!")
        sys.exit(1)

    passed = 0
    failed = 0
    failures = []

    print(f"Running {len(files)} tests with dcc: {dcc_path}")
    print("=" * 60)

    for decaf_file in files:
        rel_path = os.path.relpath(decaf_file, tests_dir)
        expect_error = is_expected_to_fail(decaf_file)
        ok, retcode, stderr_text = run_test(dcc_path, decaf_file, expect_error)

        if ok:
            passed += 1
            status = "PASS"
        else:
            failed += 1
            status = "FAIL"
            failures.append((rel_path, expect_error, retcode, stderr_text))

        expected = "error" if expect_error else "success"
        print(f"  [{status}] {rel_path:40s} (expected {expected}, got exit={retcode})")

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {len(files)} total")

    if failures:
        print("\nFailed tests:")
        for rel_path, expect_error, retcode, stderr_text in failures:
            expected = "error" if expect_error else "success"
            print(f"  - {rel_path}: expected {expected}, got exit={retcode}")
            if stderr_text.strip():
                for line in stderr_text.strip().split("\n")[:3]:
                    print(f"      {line}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
