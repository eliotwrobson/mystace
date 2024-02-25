# import random

import typing as t

import chevron
import pytest
from typing_extensions import assert_never

from chevron2.renderer import render

RenderFunctionT = t.Literal["chevron2", "chevron"]


@pytest.mark.parametrize("render_function_name", t.get_args(RenderFunctionT))
def test_large(render_function_name: RenderFunctionT, benchmark) -> None:
    n = 10_000

    if render_function_name == "chevron2":
        render_function = render
    elif render_function_name == "chevron":
        render_function = chevron.render
    else:
        assert_never(render_function_name)

    names = {f"thing{i}": i for i in range(n)}
    template = "".join(r"{{" + name + "}}" for name in names.keys())

    benchmark(render_function, template, names)
