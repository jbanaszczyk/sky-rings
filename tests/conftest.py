import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(ROOT, "src"), os.path.join(ROOT, "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import helpers  # noqa: E402


@pytest.fixture(scope="session")
def reference_cases():
    return helpers.load_cases("reference_positions.jsonl")


def pytest_terminal_summary(terminalreporter):
    if not helpers.ERROR_SUMMARY:
        return
    terminalreporter.write_sep("-", "skyengine vs reference: angular separation (degrees)")
    terminalreporter.write_line("%-8s %6s %8s %8s %8s" % ("body", "n", "max", "mean", "tol"))
    for name, stats in helpers.ERROR_SUMMARY.items():
        terminalreporter.write_line("%-8s %6d %8.4f %8.4f %8.2f" % (
            name, stats["n"], stats["max"], stats["mean"], stats["tol"]))
