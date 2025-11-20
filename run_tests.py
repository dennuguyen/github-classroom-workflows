import argparse
import os
import json
import subprocess
import tempfile

from shm_manager import SharedMemoryManager
from testing_model import TestSuite

SANITISER_ERROR = 2

test_env_vars = {
    "ASAN_OPTIONS": f"print_summary=1:verbosity=0:exitcode={SANITISER_ERROR}"
}


def _extract_sanitiser_summary(sanitiser_summary: str) -> str:
    """
    Sanitisers will print a lot of hard-to-read junk so this function collects
    the line that starts with SUMMARY:
    """
    prefix = "SUMMARY:"
    return next(
        (
            line.removeprefix(prefix).strip()
            for line in sanitiser_summary.splitlines()
            if line.startswith(prefix)
        ),
        "",
    )


def _run_tests(test_executable: str, suite: TestSuite, timeout: float) -> TestSuite:
    for test in suite.tests:
        test.passed = False

        # Run test.
        with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8") as temp:
            with SharedMemoryManager("timeout", 1024) as shm:
                shm.write_double(0, test.timeout)  # per test-case timeout

                out = subprocess.run(
                    [
                        test_executable,
                        f"--gtest_filter={test.id}",
                        f"--gtest_output=json:{temp.name}",
                    ],
                    env={**os.environ, **test_env_vars},
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    preexec_fn=os.setsid,
                    timeout=timeout,  # last resort timeout
                )

                if out.returncode == SANITISER_ERROR:
                    test.feedback = _extract_sanitiser_summary(
                        out.stderr.decode("utf-8", errors="replace")
                    )
                    continue

                if out.returncode not in (0, 1):
                    if "observed" not in test or test["observed"] == "":
                        test.feedback = "Uncaught runtime error"
                        continue

                # Test did not output anything.
                testworld_detail = json.load(temp)
                if "testsuites" not in testworld_detail:
                    test.feedback = "Test timed out"
                    continue

                # Get runtime metadata from running tests.
                testsuite_detail = testworld_detail["testsuites"][0]
                testcase_detail = testsuite_detail["testsuite"][0]
                test.passed = not testsuite_detail["failures"]
                test.score = testcase_detail.get("score", test.score)
                test.min_score = testcase_detail.get("min_score", test.min_score)
                test.max_score = testcase_detail.get("max_score", test.max_score)
                test.hidden = testcase_detail.get("hidden", False)
                test.secret = testcase_detail.get("secret", False)
                test.expected = testcase_detail.get("expected", None)
                test.observed = testcase_detail.get("observed", None)
                if "failures" in testcase_detail:
                    test.feedback = testcase_detail["failures"][0]["failure"]
    return suite


def _normalise_scores(suite: TestSuite) -> TestSuite:
    """
    Re-adjust scores and penalties.
    """
    for test in suite.tests:
        test.score = test.score or test.max_score if test.passed else test.min_score
        test.score = max(test.score, test.min_score)
        test.score = min(test.score, test.max_score)
        suite.score += test.score
        suite.max_score += test.max_score
    return suite


def run_tests(
    test_executable: str,
    test_config: str,
    output_file: str = None,
    timeout: float = None,
) -> str:
    suite = TestSuite(**json.load(open(test_config, "r")))
    suite = _run_tests(test_executable, suite, timeout)
    suite = _normalise_scores(suite)
    output = suite.model_dump_json()

    # Write JSON to output file if provided.
    if output_file:
        with open(output_file, "w") as f:
            f.write(output)

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="run_tests",
        description="Run tests",
    )
    parser.add_argument("test_executable")
    parser.add_argument("test_configuration")
    parser.add_argument("-o", "--output", default=None)
    parser.add_argument("-t", "--timeout", default=None)
    args = parser.parse_args()

    output = run_tests(
        args.test_executable,
        args.test_configuration,
        args.output,
        args.timeout,
    )
    print(output)
