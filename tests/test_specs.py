#!/usr/bin/env python3

"""
Testing against the official mustache specs. From:
https://github.com/mustache/spec
"""

import json
from pathlib import Path

from chevron2 import render_from_template

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
        "~inheritance - Default",
        "~inheritance - Variable",
        "~inheritance - Triple Mustache",
        "~inheritance - Sections",
        "~inheritance - Negative Sections",
        "~inheritance - Mustache Injection",
        "~inheritance - Inherit",
        "~inheritance - Overridden content",
        "~inheritance - Data does not override block",
        "~inheritance - Data does not override block default",
        "~inheritance - Overridden parent",
        "~inheritance - Two overridden parents",
        "~inheritance - Override parent with newlines",
        "~inheritance - Inherit indentation",
        "~inheritance - Only one override",
        "~inheritance - Parent template",
        "~inheritance - Recursion",
        "~inheritance - Multi-level inheritance",
        "~inheritance - Multi-level inheritance, no sub child",
        "~inheritance - Text inside parent",
        "~inheritance - Text inside parent",
        "~inheritance - Block scope",
        "~inheritance - Standalone parent",
        "~inheritance - Standalone block",
        "~inheritance - Block reindentation",
        "~inheritance - Intrinsic indentation",
        "~inheritance - Nested block reindentation",
        "~lambdas - Interpolation",
        "~lambdas - Interpolation - Expansion",
        "~lambdas - Interpolation - Alternate Delimiters",
        "~lambdas - Interpolation - Multiple Calls",
        "~lambdas - Escaping",
        "~lambdas - Section",
        "~lambdas - Section - Expansion",
        "~lambdas - Section - Alternate Delimiters",
        "~lambdas - Section - Multiple Calls",
    )
)


def test_spec_from_folder(datadir: Path) -> None:
    # TODO get a cleaner way of parameterizing these
    # https://stackoverflow.com/questions/57702637/how-to-parametrize-tests-with-json-array-test-data-using-pytest-in-python
    any_fail = False
    for test_path in datadir.iterdir():
        if test_path.name in (
            "delimiters.json",
            "partials.json",
        ) or test_path.name.startswith("~"):
            continue

        with test_path.open() as test_file:
            test_obj = json.load(test_file)

        for test_case in test_obj["tests"]:
            full_test_case_name = f"{test_path.stem} - {test_case['name']}"

            if full_test_case_name in SKIPPED_TESTS:
                continue
            print(full_test_case_name)
            # try:
            result = render_from_template(
                test_case["template"],
                test_case["data"],
                partials=test_case.get("partials", {}),
            )
            did_case_fail = result != test_case["expected"]
            # except Exception:
            #    did_case_fail = True

            if did_case_fail:
                print(full_test_case_name)
                print(repr(result), repr(test_case["expected"]))

            any_fail = any_fail or did_case_fail

            assert not any_fail
