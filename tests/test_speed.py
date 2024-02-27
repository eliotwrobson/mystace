# import random

import copy
import cProfile
import math
import os
import random
import string
import subprocess
import typing as t

import chevron
import combustache
import moosetash
import pystache
import pytest
import ustache
from faker import Faker
from typing_extensions import assert_never

import chevron2

RenderFunctionT = t.Literal[
    "chevron2", "chevron", "combustache", "moosetash", "pystache", "ustache"
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


def generate_test_case_random(seed: int) -> TestCaseGeneratorT:
    assert seed, "A falsey seed leads to nondeterminism"

    # TODO Add two more parameters to generate_test_case_random:
    # 1) A knob to control template nestedness
    # 2) A knob to control names nestedness

    def _generate(n: int) -> TestCaseT:
        # Use our own seeded Random object instead of the module's default
        # Random object
        my_random = random.Random(seed)

        names = {}

        def gen_template(n):
            if n > 0:
                num_sections = my_random.randint(
                    math.floor(n ** (1 / 3)), math.ceil(n ** (2 / 3))
                )
                num_template_items = my_random.randint(
                    math.floor(n ** (1 / 3)), math.ceil(n ** (2 / 3))
                )

                section_sizes = [0] * num_sections
                for i in range(n - num_template_items):
                    section_sizes[my_random.randint(0, num_sections - 1)] += 1

                while num_sections or num_template_items:
                    if (
                        my_random.randint(0, num_sections + num_template_items - 1)
                        < num_sections
                    ):
                        section_n = section_sizes.pop()
                        num_sections -= 1
                        yield from gen_section(section_n)
                    else:
                        num_template_items -= 1
                        yield from gen_template_item()

        def gen_template_item():
            yield from my_random.choice(
                [
                    # gen_partial,
                    gen_comment,
                    gen_unescaped_variable_amp,
                    gen_unescaped_variable,
                    gen_variable,
                    gen_verbatim,
                ]
            )()

        def gen_section(n):
            # open section
            yield whitespace()
            yield "{{"
            yield my_random.choice(["#", "^"])
            yield whitespace()
            var = variable_name()
            yield var
            yield whitespace()
            yield "}}"
            yield whitespace()

            yield from gen_template(n - 1)

            # close section
            yield whitespace()
            yield "{{/"
            yield whitespace()
            yield var
            yield whitespace()
            yield "}}"
            yield whitespace()

        def gen_comment():
            yield whitespace()
            yield "{{!"
            yield whitespace()
            yield verbatim()
            yield whitespace()
            yield "}}"
            yield whitespace()

        def gen_unescaped_variable():
            yield whitespace()
            yield "{{{"
            yield whitespace()
            yield variable_name()
            yield whitespace()
            yield "}}}"
            yield whitespace()

        def gen_unescaped_variable_amp():
            yield whitespace()
            yield "{{&"
            yield whitespace()
            yield variable_name()
            yield whitespace()
            yield "}}"
            yield whitespace()

        def gen_variable():
            yield whitespace()
            yield "{{"
            yield whitespace()
            yield variable_name()
            yield whitespace()
            yield "}}"
            yield whitespace()

        def variable_name():
            nonlocal names

            # TODO Currently, this only does top-level names. We will
            # want to also intelligently use dotted and context-relative
            # names, in order to get a better idea of performance.

            alphabet = string.ascii_letters
            var = "".join(
                my_random.choice(alphabet) for _ in range(my_random.randint(5, 15))
            )

            names[var] = verbatim()

            return var

        def whitespace():
            # I planned to use more whitespace characters, but that seems to
            # causes isues.
            alphabet = " "
            return "".join(
                my_random.choice(alphabet) for _ in range(my_random.randint(0, 3))
            )

        def verbatim():
            alphabet = string.ascii_letters + string.digits + " "
            return "".join(
                my_random.choice(alphabet) for _ in range(my_random.randint(10, 100))
            )

        def gen_verbatim():
            yield verbatim()

        template = "".join(gen_template(n))
        return template, names

    _generate.__name__ = f"generate_test_case_random_with_seed_{seed}"

    return _generate


@pytest.mark.parametrize("render_function_name", t.get_args(RenderFunctionT))
@pytest.mark.parametrize(
    "test_case_generator",
    [generate_test_case_nested, generate_test_case_long, generate_test_case_random(1)],
)
def test_large(
    render_function_name: RenderFunctionT,
    test_case_generator: TestCaseGeneratorT,
    benchmark,
    request,
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
    elif render_function_name == "ustache":
        render_function = pystache.render
    else:
        assert_never(render_function_name)

    template, names = test_case_generator(n)

    os.makedirs("cprofile_stats", exist_ok=True)
    my_locals = locals()
    my_locals["res"] = None
    cProfile.runctx(
        "res = benchmark(render_function, template, names)",
        globals(),
        my_locals,
        f"cprofile_stats/{request.node.name}.cprofile",
    )
    res = my_locals["res"]
    subprocess.Popen(
        f"flameprof cprofile_stats/{request.node.name}.cprofile > cprofile_stats/{request.node.name}.svg",
        shell=True,
    )

    # Chevron interface is always the reference
    assert res == chevron.render(template, names)
