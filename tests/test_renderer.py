#!/usr/bin/python
# -*- coding: utf-8 -*-

import collections
import typing as t

import pytest
from chevron2 import (
    DelimiterError,
    MissingClosingTagError,
    StrayClosingTagError,
    render_from_template,
)

# TODO get test cases from here https://gitlab.com/ergoithz/ustache/-/blob/master/tests.py?ref_type=heads
# and here https://github.com/michaelrccurtis/moosetash/blob/main/tests/test_context.py


def test_mini() -> None:
    n = 10
    names = {f"thing{i}": i for i in range(n)}
    template = "".join(R"{{" + name + R"}}" for name in names.keys())

    expected = "".join(str(i) for i in range(n))

    res = render_from_template(template, names)
    assert expected == res


# Tests adapted from: https://github.com/noahmorrison/chevron/blob/main/test_spec.py


def test_unclosed_sections() -> None:
    test1 = {"template": "{{# section }} oops {{/ wrong_section }}"}

    test2 = {"template": "{{# section }} end of file"}

    with pytest.raises(Exception):
        render_from_template(**test1)  # type: ignore
        render_from_template(**test2)  # type: ignore


def test_unicode_basic() -> None:
    args = {"template": "(╯°□°）╯︵ ┻━┻"}

    result = render_from_template(**args)  # type: ignore
    expected = "(╯°□°）╯︵ ┻━┻"

    assert result == expected


def test_unicode_variable() -> None:
    args = {"template": "{{ table_flip }}", "data": {"table_flip": "(╯°□°）╯︵ ┻━┻"}}

    result = render_from_template(**args)  # type: ignore
    expected = "(╯°□°）╯︵ ┻━┻"

    assert result == expected


def test_unicode_partial() -> None:
    args = {
        "template": "{{> table_flip }}",
        "partials": {"table_flip": "(╯°□°）╯︵ ┻━┻"},
    }

    result = render_from_template(**args)  # type: ignore
    expected = "(╯°□°）╯︵ ┻━┻"

    assert result == expected


def test_missing_key_partial() -> None:
    args = {
        "template": "before, {{> with_missing_key }}, after",
        "partials": {
            "with_missing_key": "{{#missing_key}}bloop{{/missing_key}}",
        },
    }

    result = render_from_template(**args)  # type: ignore
    expected = "before, , after"

    assert result == expected


def test_listed_data() -> None:
    args = {"template": "{{# . }}({{ . }}){{/ . }}", "data": [1, 2, 3, 4, 5]}

    result = render_from_template(**args)  # type: ignore
    expected = "(1)(2)(3)(4)(5)"

    assert result == expected


def test_recursion() -> None:
    args = {
        "template": "{{# 1.2 }}{{# data }}{{.}}{{/ data }}{{/ 1.2 }}",
        "data": {"1": {"2": [{"data": ["1", "2", "3"]}]}},
    }

    result = render_from_template(**args)  # type: ignore
    expected = "123"

    assert result == expected


def test_unicode_inside_list() -> None:
    args = {"template": "{{#list}}{{.}}{{/list}}", "data": {"list": ["☠"]}}

    result = render_from_template(**args)  # type: ignore
    expected = "☠"

    assert result == expected


def test_falsy() -> None:
    # NOTE the expected output differs from the original test case
    # https://github.com/noahmorrison/chevron/blob/main/test_spec.py#L178
    args = {
        "template": "{{null}}{{false}}{{list}}{{dict}}{{zero}}",
        "data": {"null": None, "false": False, "list": [], "dict": {}, "zero": 0},
    }

    result = render_from_template(**args)  # type: ignore
    expected = R"False[]{}0"

    assert result == expected


# TODO https://github.com/eliotwrobson/chevron2/issues/3
# def test_complex():
#     class Complex:
#         def __init__(self):
#             self.attr = 42

#     args = {
#         "template": "{{comp.attr}} {{int.attr}}",
#         "data": {"comp": Complex(), "int": 1},
#     }

#     result = render(**args)
#     expected = "42 "

#     assert result == expected


# https://github.com/noahmorrison/chevron2/issues/17
def test_inverted_coercion() -> None:
    args = {
        "template": "{{#object}}{{^child}}{{.}}{{/child}}{{/object}}",
        "data": {"object": ["foo", "bar", {"child": True}, "baz"]},
    }

    result = render_from_template(**args)  # type: ignore
    expected = "foobarbaz"

    assert result == expected


def test_closing_tag_only() -> None:
    # NOTE the expected output differs from the original test case
    # https://github.com/noahmorrison/chevron/blob/main/test_spec.py#L225
    args = {"template": "{{ foo } bar", "data": {"foo": "xx"}}

    # with pytest.raises(Chevron2Error):
    res = render_from_template(**args)  # type: ignore
    expected = "{{ foo } bar"

    assert res == expected


def test_current_line_rest() -> None:
    # NOTE the expected output differs from the original test case
    # https://github.com/noahmorrison/chevron/blob/main/test_spec.py#L233
    args = {"template": "first line\nsecond line\n {{ foo } bar", "data": {"foo": "xx"}}

    res = render_from_template(**args)  # type: ignore
    expected = "first line\nsecond line\n {{ foo } bar"

    assert res == expected


def test_no_opening_tag() -> None:
    args = {
        "template": "oops, no opening tag {{/ closing_tag }}",
        "data": {"foo": "xx"},
    }

    with pytest.raises(StrayClosingTagError):
        render_from_template(**args)  # type: ignore


# https://github.com/noahmorrison/chevron/issues/17
# def test_callable_1():
#     args_passed = {}

#     def first(content, render):
#         args_passed["content"] = content
#         args_passed["render"] = render

#         return "not implemented"

#     args = {
#         "template": "{{{postcode}}} {{#first}} {{{city}}} || {{{town}}} "
#         "|| {{{village}}} || {{{state}}} {{/first}}",
#         "data": {
#             "postcode": "1234",
#             "city": "Mustache City",
#             "state": "Nowhere",
#             "first": first,
#         },
#     }

#     result = render(**args)
#     expected = "1234 not implemented"
#     template_content = (
#         " {{& city }} || {{& town }} || {{& village }} " "|| {{& state }} "
#     )

#     assert result == expected
#     assert args_passed["content"] == template_content


# def test_callable_2():

#     def first(content, render):
#         result = render(content)
#         result = [x.strip() for x in result.split(" || ") if x.strip()]
#         return result[0]

#     args = {
#         "template": "{{{postcode}}} {{#first}} {{{city}}} || {{{town}}} "
#         "|| {{{village}}} || {{{state}}} {{/first}}",
#         "data": {
#             "postcode": "1234",
#             "town": "Mustache Town",
#             "state": "Nowhere",
#             "first": first,
#         },
#     }

#     result = render(**args)
#     expected = "1234 Mustache Town"

#     assert result == expected


# def test_callable_3():
#     """Test generating some data within the function"""

#     def first(content, render):
#         result = render(content, {"city": "Injected City"})
#         result = [x.strip() for x in result.split(" || ") if x.strip()]
#         return result[0]

#     args = {
#         "template": "{{{postcode}}} {{#first}} {{{city}}} || {{{town}}} "
#         "|| {{{village}}} || {{{state}}} {{/first}}",
#         "data": {
#             "postcode": "1234",
#             "town": "Mustache Town",
#             "state": "Nowhere",
#             "first": first,
#         },
#     }

#     result = render(**args)
#     expected = "1234 Injected City"

#     assert result == expected


# def test_callable_4():
#     """Test render of partial inside lambda"""

#     def function(content, render):
#         return render(content)

#     args = {
#         "template": "{{#function}}{{>partial}}{{!comment}}{{/function}}",
#         "partials": {
#             "partial": "partial content",
#         },
#         "data": {
#             "function": function,
#         },
#     }

#     result = render(**args)
#     expected = "partial content"

#     assert result == expected


# https://github.com/noahmorrison/chevron/issues/39
def test_nest_loops_with_same_key() -> None:
    args = {"template": "A{{#x}}B{{#x}}{{.}}{{/x}}C{{/x}}D", "data": {"x": ["z", "x"]}}

    result = render_from_template(**args)  # type: ignore
    expected = "ABzxCBzxCD"

    assert result == expected


# https://github.com/noahmorrison/chevron/issues/49
# TODO fix partial indentation behavior
@pytest.mark.xfail
def test_partial_indentation() -> None:
    args = {"template": "\t{{> count }}", "partials": {"count": "\tone\n\ttwo"}}

    result = render_from_template(**args)  # type: ignore
    expected = "\t\tone\n\t\ttwo"

    assert result == expected


# https://github.com/noahmorrison/chevron/issues/52
# TODO implement this and feed in lambdas test cases.
@pytest.mark.xfail
def test_indexed() -> None:
    args = {
        "template": "count {{count.0}}, {{count.1}}, " "{{count.100}}, {{nope.0}}",
        "data": {
            "count": [5, 4, 3, 2, 1],
        },
    }

    result = render_from_template(**args)  # type: ignore
    expected = "count 5, 4, , "

    assert result == expected


# TODO enable once I get partials working properly
# def test_iterator_scope_indentation():
#     args = {
#         "data": {
#             "thing": ["foo", "bar", "baz"],
#         },
#         "template": "{{> count }}",
#         "partials": {
#             "count": "    {{> iter_scope }}",
#             "iter_scope": "foobar\n{{#thing}}\n {{.}}\n{{/thing}}",
#         },
#     }

#     result = render(**args)
#     expected = "    foobar\n     foo\n     bar\n     baz\n"

#     assert result == expected


# https://github.com/noahmorrison/chevron/pull/73
@pytest.mark.xfail
def test_namedtuple_data() -> None:
    NT = collections.namedtuple("NT", ["foo", "bar"])
    args = {"template": "{{foo}} {{bar}}", "data": NT("hello", "world")}

    result = render_from_template(**args)  # type: ignore
    expected = "hello world"

    assert result == expected


@pytest.mark.xfail
def test_get_key_not_in_dunder_dict_returns_attribute() -> None:
    class C:
        foo = "bar"

    instance = C()
    assert "foo" not in instance.__dict__

    args = {"template": "{{foo}}", "data": instance}
    result = render_from_template(**args)  # type: ignore
    expected = "bar"

    assert result == expected


# https://github.com/noahmorrison/chevron/pull/94
# TODO try to add this attribute later.
# def test_keep():
#     args = {
#         "template": "{{ first }} {{ second }} {{ third }}",
#         "data": {
#             "first": "1st",
#             "third": "3rd",
#         },
#     }

#     result = render(**args)
#     expected = "1st  3rd"
#     assert result == expected

#     args["keep"] = True

#     result = render(**args)
#     expected = "1st {{ second }} 3rd"
#     assert result == expected

#     args["template"] = "{{first}} {{second}} {{third}}"
#     result = render(**args)
#     expected = "1st {{ second }} 3rd"
#     assert result == expected

#     args["template"] = "{{   first    }} {{    second    }} {{    third   }}"
#     result = render(**args)
#     expected = "1st {{ second }} 3rd"
#     assert result == expected


# https://github.com/noahmorrison/chevron/pull/94
# def test_keep_from_partials():
#     args = {
#         "template": "{{ first }} {{> with_missing_key }} {{ third }}",
#         "data": {
#             "first": "1st",
#             "third": "3rd",
#         },
#         "partials": {
#             "with_missing_key": "{{missing_key}}",
#         },
#     }

#     result = render(**args)
#     expected = "1st  3rd"
#     assert result == expected

#     args["keep"] = True

#     result = render(**args)
#     expected = "1st {{ missing_key }} 3rd"
#     assert result == expected


# Tests below from
# https://github.com/sakhezech/combustache/blob/main/tests/custom/test_bad_template.py
def test_left_delimiter_eof() -> None:
    template = "{{"
    data: t.Dict = {}

    assert template == render_from_template(template, data)


def test_no_content_tag() -> None:
    # NOTE output differs from original test case.
    template = "{{}}"
    data: t.Dict = {"": "stuff"}

    assert "stuff" == render_from_template(template, data)


@pytest.mark.xfail
def test_bad_delimiter() -> None:
    template = "{{= a a a =}}"
    data: t.Dict = {}

    with pytest.raises(DelimiterError):
        render_from_template(template, data)


@pytest.mark.xfail
def test_section_not_closed() -> None:
    template = "{{#section}} hello"
    data: t.Dict = {}

    with pytest.raises(MissingClosingTagError):
        render_from_template(template, data)


def test_stray_closing_tag() -> None:
    template = "{{/closing}} hello"
    data: t.Dict = {}

    with pytest.raises(StrayClosingTagError):
        render_from_template(template, data)


# Tests below from:
# https://github.com/sakhezech/combustache/blob/main/tests/custom/test_opts.py


@pytest.mark.xfail
def test_stringify():
    template = "This statement is {{bool}}."
    data = {"bool": True}
    expected = "This statement is true."

    def lowercase_bool(val):
        if val is None:
            return ""
        if isinstance(val, bool):
            return str(val).lower()
        return str(val)

    out = render_from_template(template, data, stringify=lowercase_bool)
    assert out == expected


# See also:
# https://github.com/noahmorrison/chevron/issues/125
@pytest.mark.xfail
def test_escape():
    template = "I am escaping quotes: {{quotes}}"
    data = {"quotes": "\" \" ' '"}
    expected = r"I am escaping quotes: \" \" \' \'"

    def escape_quotes(string: str) -> str:
        return string.replace("'", r"\'").replace('"', r"\"")

    out = render_from_template(template, data, escape=escape_quotes)
    assert out == expected


# TODO give a default option that is to emit a warning, or do whatever chevron does
# https://github.com/noahmorrison/chevron/blob/main/chevron/renderer.py#L95
@pytest.mark.xfail
def test_missing_data():
    template = "Location: {{location}}."
    data = {}
    expected = "Location: UNKNOWN."

    out = render_from_template(template, data, missing_data=lambda: "UNKNOWN")
    assert out == expected

    def raise_if_missing():
        raise ValueError("MISSING DATA")

    with pytest.raises(ValueError):
        out = render_from_template(template, data, missing_data=raise_if_missing)

    # None is not missing data
    data = {"location": None}
    expected = "Location: ."
    out = render_from_template(template, data, missing_data=lambda: "UNKNOWN")
    assert out == expected


@pytest.mark.xfail
def test_missing_partial():
    template = "{{>cool_partial}}"
    data = {"part_of_partial": 321}
    partials = {}
    expected = "(Partial failed to load!)"

    out = render_from_template(
        template,
        data,
        partials,
        missing_data=lambda: "(Partial failed to load!)",
    )
    assert out == expected


@pytest.mark.xfail
def test_missing_section():
    template = "List of your repos:{{#repos}}\n[{{name}}](url) - {{desc}}{{/repos}}"
    data = {"repos": []}
    expected = "List of your repos:"
    out = render_from_template(
        template, data, missing_data=lambda: " you have no repos :("
    )
    assert out == expected
    data = {"repos": None}

    out = render_from_template(
        template, data, missing_data=lambda: " you have no repos :("
    )
    assert out == expected

    data = {}
    expected = "List of your repos: you have no repos :("
    out = render_from_template(
        template, data, missing_data=lambda: " you have no repos :("
    )
    assert out == expected
