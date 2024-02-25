# import random

import copy
import typing as t

import chevron
import combustache
import moosetash
import pystache
import pytest
from faker import Faker
from typing_extensions import assert_never

import chevron2

RenderFunctionT = t.Literal[
    "chevron2", "chevron", "combustache", "moosetash", "pystache"
]
TestCaseT = t.Tuple[str, t.Dict[str, int]]
TestCaseGeneratorT = t.Callable[[int], TestCaseT]


def generate_test_case_long(n: int) -> TestCaseT:
    names = {f"thing{i}": i for i in range(n)}
    template = "".join(r"{{" + name + "}}" for name in names.keys())

    return template, names


def generate_test_case_nested(n: int) -> TestCaseT:
    fake = Faker()

    def _runner(n: int) -> TestCaseT:
        if n <= 1:
            curr_name = fake.unique.word()
            curr_data = fake.unique.word()
            return "{{" + curr_name + "}}", {curr_name: curr_data}

        old_template, old_data = _runner(n // 2)

        curr_name = fake.unique.word()
        data_dict = {curr_name: [copy.deepcopy(old_data), copy.deepcopy(old_data)]}
        template = "{{#" + curr_name + "}}" + old_template + "{{/" + curr_name + "}}"
        return template, data_dict

    return _runner(n)


@pytest.mark.parametrize("render_function_name", t.get_args(RenderFunctionT))
@pytest.mark.parametrize(
    "test_case_generator", [generate_test_case_nested, generate_test_case_long]
)
def test_large(
    render_function_name: RenderFunctionT,
    test_case_generator: TestCaseGeneratorT,
    benchmark,
) -> None:
    n = 1000

    if render_function_name == "chevron2":
        render_function = chevron2.render
    elif render_function_name == "chevron":
        render_function = chevron.render
    elif render_function_name == "combustache":
        render_function = combustache.render
    elif render_function_name == "moosetash":
        # Use the fast mode for this
        render_function = moosetash.render
    elif render_function_name == "pystache":
        render_function = pystache.render
    else:
        assert_never(render_function_name)

    template, names = test_case_generator(n)

    res = benchmark(render_function, template, names)

    # Chevron interface is always the reference
    assert res == chevron.render(template, names)
