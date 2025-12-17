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
from typing import Any

import pytest

from mystace import render_from_template

# Files with features not yet fully implemented
EXPECTED_FAIL_FILES = {
    "~dynamic-names.json",
    "~inheritance.json",
    "~lambdas.json",
}


def load_spec_tests(datadir: Path) -> list[tuple[str, dict[str, Any], bool]]:
    """Load all test cases from spec JSON files."""
    test_cases = []
    for test_path in datadir.iterdir():
        if not test_path.name.endswith(".json"):
            continue

        with test_path.open() as test_file:
            test_obj = json.load(test_file)

        should_xfail = test_path.name in EXPECTED_FAIL_FILES

        for test_case in test_obj["tests"]:
            test_id = f"{test_path.stem}::{test_case['name']}"
            test_cases.append((test_id, test_case, should_xfail))

    return test_cases


@pytest.fixture(scope="module")
def spec_test_cases(datadir: Path) -> list[tuple[str, dict[str, Any], bool]]:
    """Fixture that loads all spec test cases once per module."""
    return load_spec_tests(datadir)


@pytest.mark.parametrize(
    "test_id,test_case,should_xfail",
    [
        pytest.param(*case, id=case[0])
        for case in load_spec_tests(Path(__file__).parent / "test_specs")
    ],
)
def test_mustache_spec(
    test_id: str, test_case: dict[str, Any], should_xfail: bool
) -> None:
    """Test individual mustache spec cases."""
    if should_xfail:
        pytest.xfail(f"Feature not yet implemented: {test_id}")

    result = render_from_template(
        test_case["template"],
        test_case["data"],
        partials=test_case.get("partials", None),
    )

    assert result == test_case["expected"], (
        f"\nTemplate: {test_case['template']!r}\n"
        f"Data: {test_case['data']!r}\n"
        f"Expected: {test_case['expected']!r}\n"
        f"Got: {result!r}"
    )
