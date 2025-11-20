import difflib
import json
import shutil
import sys

from actions_toolkit import core
from colored import Fore, Back, Style
from testing_model import TestCase, TestSuite


def _print_diff(text1: str, text2: str) -> str:
    text1 = text1 or ""
    text2 = text2 or ""
    columns = shutil.get_terminal_size().columns
    diff = difflib.ndiff(text1.splitlines(), text2.splitlines())
    for line in diff:
        if line.startswith("+"):
            print(f"{Back.green_4}{line:<{columns}}{Style.reset}")
        elif line.startswith("-"):
            print(f"{Back.dark_red_1}{line:<{columns}}{Style.reset}")
        else:
            print(line)


def print_testcase(test: TestCase) -> bool:
    line = "{style}{icon} {name}{point}{reset}"
    show_feedback = None
    format = {"style": "", "icon": "", "name": "", "point": "", "reset": Style.reset}

    if test.secret:
        return test.passed

    if test.passed:
        format["style"] = f"{Fore.green}{Style.bold}"
        format["icon"] = "✅"
    else:
        format["style"] = f"{Fore.red}{Style.bold}"
        format["icon"] = "❌"
        if not test.hidden:

            def show_feedback(feedback, expected, observed):
                return (
                    core.start_group("Feedback"),
                    print(feedback) if feedback else None,
                    print("Difference was:"),
                    _print_diff(expected, observed),
                    core.end_group(),
                )

    if test.hidden:
        format["name"] = "(hidden test)"
    else:
        format["name"] = test.name or test.id
        format["point"] = f" ({test.score}/{test.max_score})"

    line = line.format(**format)
    print(line)
    if show_feedback:
        show_feedback(test.feedback, test.expected, test.observed)


def print_testsuite(suite: TestSuite):
    print("🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀")
    line = f"{suite.name} ({suite.score}/{suite.max_score})"
    print(
        f"{Fore.green if suite.score == suite.max_score else Fore.red}{Style.bold}{line}{Style.reset}"
    )


def notify_classroom(score: int, max_score: int):
    text = f"Points {score}/{max_score}"
    core.notice(text, title="Autograding complete")

    summary = json.dumps({"totalPoints": score, "maxPoints": max_score})
    core.notice(summary, title="Autograding report")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: report.py <result_files>", file=sys.stderr)
        sys.exit(1)

    grand_score = 0
    grand_max_score = 0

    for i in range(1, len(sys.argv)):
        result = sys.argv[i]
        with open(result, "r") as f:
            suite = TestSuite(**json.load(open(result, "r")))
            print_testsuite(suite)
            for test in suite.tests:
                print_testcase(test)

            grand_score += suite.score
            grand_max_score += suite.max_score

    notify_classroom(grand_score, grand_max_score)
