#!/usr/bin/python
# -*- coding: utf-8 -*-

import copy
import cProfile
import math
import os
import random
import string
import subprocess
import typing as t
import warnings

import chevron
import chevron2
import combustache
import moosetash
import pystache
import pytest
import ustache
from faker import Faker
from typing_extensions import assert_never

RenderFunctionT = t.Literal[
    "chevron2",
    "chevron",
    "combustache",
    "moosetash",
    "pystache",
    "ustache",
    "chevron2-full",
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
        data_dict: t.Dict = {
            curr_name: [copy.deepcopy(old_data), copy.deepcopy(old_data)]
        }
        template: str = (
            "{{#" + curr_name + "}}" + old_template + "{{/" + curr_name + "}}"
        )
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

        names: t.Dict = {}

        def flatten_keys_from_scopes(scopes):
            def flatten_keys(scope):
                if scope is None:
                    return []

                ret = []
                for k, v in scope.items():
                    flat = flatten_keys(v)
                    if flat == []:
                        flat = [(k, v)]
                    else:
                        flat = [(f"{k}.{x}", v) for (x, v) in flat]
                    ret.extend(flat)
                return ret

            ret = []
            for scope in scopes:
                ret.extend(flatten_keys(scope))
            return ret

        def randomly_insert_name_into_scope(name, scope, is_section):
            key = []
            while True:
                child = my_random.choice(list(scope.keys()) + [None])
                if child is None or scope[child] is None:
                    break
                else:
                    key.append(child)
                    scope = scope[child]
            if is_section:
                val = {}
            else:
                val = None
            scope[name] = val
            key.append(name)
            return ".".join(key), val

        def gen_template(n, scopes):
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
                        yield from gen_section(section_n, scopes)
                    else:
                        num_template_items -= 1
                        yield from gen_template_item(scopes)

        def gen_template_item(scopes):
            yield from my_random.choice(
                [
                    # gen_partial,
                    gen_comment,
                    gen_unescaped_variable_amp,
                    gen_unescaped_variable,
                    gen_variable,
                    gen_verbatim,
                ]
            )(scopes)

        def gen_section(n, scopes):
            key, val = variable_name(scopes, True)
            scopes.append(val)

            # open section
            yield whitespace()
            yield "{{"
            yield my_random.choice(["#", "^"])
            yield whitespace()
            yield key
            yield whitespace()
            yield "}}"
            yield whitespace()

            yield from gen_template(n - 1, scopes)

            # close section
            yield whitespace()
            yield "{{/"
            yield whitespace()
            yield key
            yield whitespace()
            yield "}}"
            yield whitespace()

        def gen_comment(scopes):
            yield whitespace()
            yield "{{!"
            yield whitespace()
            yield verbatim()
            yield whitespace()
            yield "}}"
            yield whitespace()

        def gen_unescaped_variable(scopes):
            yield whitespace()
            yield "{{{"
            yield whitespace()
            yield variable_name(scopes, False)[0]
            yield whitespace()
            yield "}}}"
            yield whitespace()

        def gen_unescaped_variable_amp(scopes):
            yield whitespace()
            yield "{{&"
            yield whitespace()
            yield variable_name(scopes, False)[0]
            yield whitespace()
            yield "}}"
            yield whitespace()

        def gen_variable(scopes):
            yield whitespace()
            yield "{{"
            yield whitespace()
            yield variable_name(scopes, False)[0]
            yield whitespace()
            yield "}}"
            yield whitespace()

        def variable_name(scopes, is_section):
            use_existing_key = my_random.random() < 0.5
            if use_existing_key:
                candidates = [
                    (k, v)
                    for (k, v) in flatten_keys_from_scopes(scopes)
                    if (v is not None) == is_section
                ]

                if len(candidates):
                    key, val = my_random.choice(candidates)
                    return key, val

            alphabet = string.ascii_letters
            name = "".join(
                my_random.choice(alphabet) for _ in range(my_random.randint(5, 15))
            )
            scope = my_random.choice(scopes)

            key, val = randomly_insert_name_into_scope(name, scope, is_section)
            return key, val

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

        def gen_verbatim(scopes):
            yield verbatim()

        def fill_in_lists_in_names(d):
            if isinstance(d, dict):
                for k in d:
                    if d[k] is not None:
                        fill_in_lists_in_names(d[k])
                        if my_random.random() < 0.75:
                            d[k] = [
                                copy.deepcopy(d[k])
                                for i in range(my_random.randint(1, 4))
                            ]
            else:
                raise TypeError

        def fill_in_values_for_leafs(d):
            if isinstance(d, dict):
                for k in d:
                    if d[k] is None:
                        d[k] = verbatim()
                    else:
                        fill_in_values_for_leafs(d[k])
            elif isinstance(d, list):
                for i in range(len(d)):
                    if d[i] is None:
                        d[i] = verbatim()
                    else:
                        fill_in_values_for_leafs(d[i])
            else:
                raise TypeError

        # Generate the template
        template = "".join(gen_template(n, [names]))

        # Elaborate the names to sometimes include lists
        fill_in_lists_in_names(names)

        # Generate the leaf values for the keys in names
        fill_in_values_for_leafs(names)

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
    benchmark: t.Any,
    request: t.Any,
) -> None:
    # TODO turn up the test case size later.
    n = 100

    template, names = test_case_generator(n)  # type: ignore

    if render_function_name == "chevron2":
        # NOTE Benchmarking with this isn't totally cheating since some of these libraries
        # to caching, meaning that the benchmark object is timing the cached version on
        # everything past the first run.
        renderer = chevron2.MustacheRenderer.from_template(template)

        def render_function(_, obj):
            return renderer.render(obj)
    elif render_function_name == "chevron2-full":
        render_function = chevron2.render_from_template
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
        render_function = ustache.render
    else:
        assert_never(render_function_name)

    try:
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
    except Exception:
        warnings.warn(
            UserWarning(f"{request.node.name} benchmark raised an exception!!")
        )
