#!/usr/bin/python
# -*- coding: utf-8 -*-

import collections

import pytest

from chevron2 import (
    Chevron2Error,
    DelimiterError,
    MissingClosingTagError,
    StrayClosingTagError,
    render,
)


def test_unclosed_sections():
    test1 = {"template": "{{# section }} oops {{/ wrong_section }}"}

    test2 = {"template": "{{# section }} end of file"}

    with pytest.raises(Chevron2Error):
        render(**test1)
        render(**test2)


def test_bad_set_delimiter_tag():
    args = {"template": "{{= bad!}}"}

    # with pytest.raises(Chevron2Error):
    render(**args)


def test_unicode_basic():
    args = {"template": "(╯°□°）╯︵ ┻━┻"}

    result = render(**args)
    expected = "(╯°□°）╯︵ ┻━┻"

    assert result == expected


def test_unicode_variable():
    args = {"template": "{{ table_flip }}", "data": {"table_flip": "(╯°□°）╯︵ ┻━┻"}}

    result = render(**args)
    expected = "(╯°□°）╯︵ ┻━┻"

    assert result == expected


def test_unicode_partial():
    args = {
        "template": "{{> table_flip }}",
        "partials": {"table_flip": "(╯°□°）╯︵ ┻━┻"},
    }

    result = render(**args)
    expected = "(╯°□°）╯︵ ┻━┻"

    assert result == expected


def test_missing_key_partial():
    args = {
        "template": "before, {{> with_missing_key }}, after",
        "partials": {
            "with_missing_key": "{{#missing_key}}bloop{{/missing_key}}",
        },
    }

    result = render(**args)
    expected = "before, , after"

    assert result == expected


def test_listed_data():
    args = {"template": "{{# . }}({{ . }}){{/ . }}", "data": [1, 2, 3, 4, 5]}

    result = render(**args)
    expected = "(1)(2)(3)(4)(5)"

    assert result == expected


def test_recursion():
    args = {
        "template": "{{# 1.2 }}{{# data }}{{.}}{{/ data }}{{/ 1.2 }}",
        "data": {"1": {"2": [{"data": ["1", "2", "3"]}]}},
    }

    result = render(**args)
    expected = "123"

    assert result == expected


def test_unicode_inside_list():
    args = {"template": "{{#list}}{{.}}{{/list}}", "data": {"list": ["☠"]}}

    result = render(**args)
    expected = "☠"

    assert result == expected


# def test_falsy():
#     args = {
#         "template": "{{null}}{{false}}{{list}}{{dict}}{{zero}}",
#         "data": {"null": None, "false": False, "list": [], "dict": {}, "zero": 0},
#     }

#     result = render(**args)
#     expected = "False0"

#     assert result == expected


def test_complex():
    class Complex:
        def __init__(self):
            self.attr = 42

    args = {
        "template": "{{comp.attr}} {{int.attr}}",
        "data": {"comp": Complex(), "int": 1},
    }

    result = render(**args)
    expected = "42 "

    assert result == expected


# https://github.com/noahmorrison/chevron2/issues/17
# def test_inverted_coercion():
#     args = {
#         "template": "{{#object}}{{^child}}{{.}}{{/child}}{{/object}}",
#         "data": {"object": ["foo", "bar", {"child": True}, "baz"]},
#     }

#     result = render(**args)
#     expected = "foobarbaz"

#     assert result == expected


# def test_closing_tag_only():
#     args = {"template": "{{ foo } bar", "data": {"foo": "xx"}}

#     with pytest.raises(Chevron2Error):
#         render(**args)


# def test_current_line_rest():
#     args = {"template": "first line\nsecond line\n {{ foo } bar", "data": {"foo": "xx"}}

#     with pytest.raises(Chevron2Error):
#         render(**args)


def test_no_opening_tag():
    args = {
        "template": "oops, no opening tag {{/ closing_tag }}",
        "data": {"foo": "xx"},
    }

    with pytest.raises(Chevron2Error):
        render(**args)


# https://github.com/noahmorrison/chevron2/issues/17
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
def test_nest_loops_with_same_key():
    args = {"template": "A{{#x}}B{{#x}}{{.}}{{/x}}C{{/x}}D", "data": {"x": ["z", "x"]}}

    result = render(**args)
    expected = "ABzxCBzxCD"

    assert result == expected


# https://github.com/noahmorrison/chevron/issues/49
def test_partial_indentation():
    args = {"template": "\t{{> count }}", "partials": {"count": "\tone\n\ttwo"}}

    result = render(**args)
    expected = "\t\tone\n\t\ttwo"

    assert result == expected


# https://github.com/noahmorrison/chevron/issues/52
def test_indexed():
    args = {
        "template": "count {{count.0}}, {{count.1}}, " "{{count.100}}, {{nope.0}}",
        "data": {
            "count": [5, 4, 3, 2, 1],
        },
    }

    result = render(**args)
    expected = "count 5, 4, , "

    assert result == expected


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
def test_namedtuple_data():
    NT = collections.namedtuple("NT", ["foo", "bar"])
    args = {"template": "{{foo}} {{bar}}", "data": NT("hello", "world")}

    result = render(**args)
    expected = "hello world"

    assert result == expected


def test_get_key_not_in_dunder_dict_returns_attribute():
    class C:
        foo = "bar"

    instance = C()
    assert "foo" not in instance.__dict__

    args = {"template": "{{foo}}", "data": instance}
    result = render(**args)
    expected = "bar"

    assert result == expected


# https://github.com/noahmorrison/chevron/pull/94
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


def test_left_delimiter_eof():
    template = "{{"
    data = {}

    render(template, data)


def test_no_content_tag():
    template = "{{}}"
    data = {}

    render(template, data)


def test_bad_delimiter():
    template = "{{= a a a =}}"
    data = {}

    with pytest.raises(DelimiterError):
        render(template, data)


def test_section_not_closed():
    template = "{{#section}} hello"
    data = {}

    with pytest.raises(MissingClosingTagError):
        render(template, data)


def test_stray_closing_tag():
    template = "{{/closing}} hello"
    data = {}

    with pytest.raises(StrayClosingTagError):
        render(template, data)
