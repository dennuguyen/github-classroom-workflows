import argparse
import re

from pathlib import Path
from pydantic import TypeAdapter
from testing_model import TestCase, TestSuite
from typing import List, Optional, Tuple


def _extract_metadata(line: str) -> Tuple[Optional[str], Optional[str]]:
    m = re.match(r"\/\/@(\w+)\s*(.*)", line)
    if m:
        key = m.group(1)
        value = m.group(2) or True
    return key, value


def _extract_testcase_metadata(code: List[str], row: int) -> TestCase:
    """
    Scans previous lines from the given line for testcase metadata.
    """
    row -= 1
    metadata = {}
    while row >= 0 and code[row].startswith("//@"):
        key, value = _extract_metadata(code[row])
        if key:
            metadata[key] = value
        row -= 1
    return TestCase(**metadata)


def _extract_test_name(code: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Gets the test suite and case names from the TEST macro.
    """
    m = re.match(r"(TEST|TEST_F)\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)", code)
    if m:
        testsuite_name = m.group(2)
        testcase_name = m.group(3)
    return testsuite_name, testcase_name


def _discover_testcases(code: str) -> List[TestCase]:
    testcases = list[TestCase]()
    for row, line in enumerate(code):
        if line.startswith("TEST"):
            suite_name, case_name = _extract_test_name(code[row])
            if suite_name and case_name:
                metadata = _extract_testcase_metadata(code, row)
                metadata.id = f"{suite_name}.{case_name}"
                testcases.append(metadata)
    return testcases


def _discover_testsuite(code: str) -> TestSuite:
    """
    Scans the first lines of the file for testsuite metadata.
    """
    row = 0
    metadata = {}
    while code[row].startswith("//@"):
        key, value = _extract_metadata(code[row])
        if key:
            metadata[key] = value
        row += 1
    return TestSuite(**metadata)


def discover_tests(test_file: str, output_file: str = None) -> str:
    code = Path(test_file).read_text().splitlines()
    suite = _discover_testsuite(code)
    suite.name = suite.name or test_file
    tests = _discover_testcases(code)
    suite.tests = TypeAdapter(List[TestCase]).validate_python(tests)
    output = suite.model_dump_json(exclude_none=True)

    # Write JSON to output file if provided.
    if output_file:
        with open(output_file, "w") as f:
            f.write(output)

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="discover_tests",
        description="Discover tests to run",
    )
    parser.add_argument("test_file")
    parser.add_argument("-o", "--output", default=None)
    args = parser.parse_args()

    output = discover_tests(args.test_file, args.output)
    print(output)
