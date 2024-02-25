# import random

import typing as t

import chevron
import combustache
import moosetash
import pystache
import pytest
from typing_extensions import assert_never

from chevron2.renderer import render

RenderFunctionT = t.Literal[
    "chevron2", "chevron", "combustache", "moosetash", "pystache"
]


@pytest.mark.parametrize("render_function_name", t.get_args(RenderFunctionT))
def test_large(render_function_name: RenderFunctionT, benchmark) -> None:
    n = 10_000

    if render_function_name == "chevron2":
        render_function = render
    elif render_function_name == "chevron":
        render_function = chevron.render
    elif render_function_name == "combustache":
        render_function = combustache.render
    elif render_function_name == "moosetash":
        render_function = moosetash.render
    elif render_function_name == "pystache":
        render_function = pystache.render
    else:
        assert_never(render_function_name)

    names = {f"thing{i}": i for i in range(n)}
    template = "".join(r"{{" + name + "}}" for name in names.keys())

    benchmark(render_function, template, names)
