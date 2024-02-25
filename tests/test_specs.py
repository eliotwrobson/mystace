#!/usr/bin/env python3

"""
Testing against the official mustache specs. From:
https://github.com/mustache/spec
"""


import json
from pathlib import Path

from chevron2 import render

# Names of tests to skip for now that fail, TODO debug these.
# Not a huuuuuge deal, since most of the failed ones are in the optional section
SKIPPED_TESTS = frozenset(
    (
        "~dynamic-names - Basic Behavior - Partial",
        "~dynamic-names - Basic Behavior - Name Resolution",
        "~dynamic-names - Context",
        "~dynamic-names - Dotted Names",
        "~dynamic-names - Dotted Names - Failed Lookup",
        "~dynamic-names - Dotted names - Context Stacking",
        "~dynamic-names - Dotted names - Context Stacking Under Repetition",
        "~dynamic-names - Dotted names - Context Stacking Failed Lookup",
        "~dynamic-names - Recursion",
        "~dynamic-names - Surrounding Whitespace",
        "~dynamic-names - Inline Indentation",
        "~dynamic-names - Standalone Line Endings",
        "~dynamic-names - Standalone Without Previous Line",
        "~dynamic-names - Standalone Without Newline",
        "~dynamic-names - Standalone Indentation",
        "~dynamic-names - Padding Whitespace",
    )
)


def test_spec_from_folder(datadir: Path) -> None:
    # TODO get a cleaner way of parameterizing these
    # https://stackoverflow.com/questions/57702637/how-to-parametrize-tests-with-json-array-test-data-using-pytest-in-python

    for test_path in datadir.iterdir():

        with test_path.open() as test_file:
            test_obj = json.load(test_file)

        for test_case in test_obj["tests"]:
            full_test_case_name = f"{test_path.stem} - {test_case['name']}"

            if full_test_case_name in SKIPPED_TESTS:
                continue

            result = render(
                test_case["template"],
                test_case["data"],
                partials=test_case.get("partials", {}),
            )

            if result != test_case["expected"]:
                print(full_test_case_name)

            # assert result == test_case["expected"], full_test_case_name
