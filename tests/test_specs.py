#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Testing against the official mustache specs. From:
https://github.com/mustache/spec

Version copied here is v1.4.1:
https://github.com/mustache/spec/releases/tag/v1.4.1
"""

import json
from pathlib import Path

from mystace import render_from_template

# Names of tests to skip for now that fail, TODO debug these.
# Not a huuuuuge deal, all of the standard failing ones are
EXPECTED_TO_FAIL = frozenset(
    (
        "partials - Standalone Without Previous Line",
        "partials - Standalone Without Newline",
        "partials - Standalone Indentation",
    )
)


def test_spec_from_folder(datadir: Path) -> None:
    # TODO get a cleaner way of parameterizing these
    # https://stackoverflow.com/questions/57702637/how-to-parametrize-tests-with-json-array-test-data-using-pytest-in-python

    any_fail = False
    for test_path in datadir.iterdir():
        # TODO get these tests working later
        if test_path.name in (
            "delimiters.json",
            "~dynamic-names.json",
            "~inheritance.json",
            "~lambdas.json",
        ):
            continue

        with test_path.open() as test_file:
            test_obj = json.load(test_file)

        for test_case in test_obj["tests"]:
            full_test_case_name = f"{test_path.stem} - {test_case['name']}"

            result = render_from_template(
                test_case["template"],
                test_case["data"],
                partials=test_case.get("partials", None),
            )
            did_case_fail = result != test_case["expected"]

            if full_test_case_name not in EXPECTED_TO_FAIL:
                any_fail = any_fail or did_case_fail
            else:
                assert did_case_fail, full_test_case_name

    assert not any_fail
