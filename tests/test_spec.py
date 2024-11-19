#!/usr/bin/python
# -*- coding: utf-8 -*-

import collections
import unittest
import os
import json
import io
import pytest
import chevron2



# SPECS_PATH = os.path.join('spec', 'specs')
# if os.path.exists(SPECS_PATH):
#     SPECS = [path for path in os.listdir(SPECS_PATH) if path.endswith('.json')]
# else:
#     SPECS = []

# STACHE = chevron2.render


# def _test_case_from_path(json_path):
#     json_path = '%s.json' % json_path

#     class MustacheTestCase(unittest.TestCase):
#         """A simple yaml based test case"""

#         def _test_from_object(obj):
#             """Generate a unit test from a test object"""

#             def test_case(self):
#                 result = STACHE(obj['template'], obj['data'],
#                                 partials_dict=obj.get('partials', {}))

#                 self.assertEqual(result, obj['expected'])

#             test_case.__doc__ = 'suite: {0}    desc: {1}'.format(spec,
#                                                                  obj['desc'])
#             return test_case

#         with io.open(json_path, 'r', encoding='utf-8') as f:
#             yaml = json.load(f)

#         # Generates a unit test for each test object
#         for i, test in enumerate(yaml['tests']):
#             vars()['test_' + str(i)] = _test_from_object(test)

#     # Return the built class
#     return MustacheTestCase


# # Create TestCase for each json file
# for spec in SPECS:
#     # Ignore optional tests
#     if spec[0] != '~':
#         spec = spec.split('.')[0]
#         globals()[spec] = _test_case_from_path(os.path.join(SPECS_PATH, spec))

#### TODO tests above need to be refactored.


def test_unclosed_sections():
    test1 = {
        'template': '{{# section }} oops {{/ wrong_section }}'
    }

    test2 = {
        'template': '{{# section }} end of file'
    }

    with pytest.raises(chevron2.ChevronError):
        chevron2.render(**test1)
        chevron2.render(**test2)

    with pytest.raises(SyntaxError):
        chevron2.render(**test1)

def test_bad_set_delimiter_tag():
    args = {
        'template': '{{= bad!}}'
    }

    with pytest.raises(SyntaxError):
        chevron2.render(**args)

def test_unicode_basic():
    args = {
        'template': '(╯°□°）╯︵ ┻━┻'
    }

    result = chevron2.render(**args)
    expected = '(╯°□°）╯︵ ┻━┻'

    assert result == expected

def test_unicode_variable():
    args = {
        'template': '{{ table_flip }}',
        'data': {'table_flip': '(╯°□°）╯︵ ┻━┻'}
    }

    result = chevron2.render(**args)
    expected = '(╯°□°）╯︵ ┻━┻'

    assert result == expected

def test_unicode_partial():
    args = {
        'template': '{{> table_flip }}',
        'partials_dict': {'table_flip': '(╯°□°）╯︵ ┻━┻'}
    }

    result = chevron2.render(**args)
    expected = '(╯°□°）╯︵ ┻━┻'

    assert result == expected

def test_missing_key_partial():
    args = {
        'template': 'before, {{> with_missing_key }}, after',
        'partials_dict': {
            'with_missing_key': '{{#missing_key}}bloop{{/missing_key}}',
        },
    }

    result = chevron2.render(**args)
    expected = 'before, , after'

    assert result == expected

def test_listed_data():
    args = {
        'template': '{{# . }}({{ . }}){{/ . }}',
        'data': [1, 2, 3, 4, 5]
    }

    result = chevron2.render(**args)
    expected = '(1)(2)(3)(4)(5)'

    assert result == expected

def test_recursion():
    args = {
        'template': '{{# 1.2 }}{{# data }}{{.}}{{/ data }}{{/ 1.2 }}',
        'data': {'1': {'2': [{'data': ["1", "2", "3"]}]}}
    }

    result = chevron2.render(**args)
    expected = '123'

    assert result == expected

def test_unicode_inside_list():
    args = {
        'template': '{{#list}}{{.}}{{/list}}',
        'data': {'list': ['☠']}
    }

    result = chevron2.render(**args)
    expected = '☠'

    assert result == expected

def test_falsy():
    args = {
        'template': '{{null}}{{false}}{{list}}{{dict}}{{zero}}',
        'data': {'null': None,
                    'false': False,
                    'list': [],
                    'dict': {},
                    'zero': 0
                    }
    }

    result = chevron2.render(**args)
    expected = 'False0'

    assert result == expected

def test_complex():
    class Complex:
        def __init__(self):
            self.attr = 42

    args = {
        'template': '{{comp.attr}} {{int.attr}}',
        'data': {'comp': Complex(),
                    'int': 1
                    }
    }

    result = chevron2.render(**args)
    expected = '42 '

    assert result == expected

# https://github.com/noahmorrison/chevron2/issues/17
def test_inverted_coercion():
    args = {
        'template': '{{#object}}{{^child}}{{.}}{{/child}}{{/object}}',
        'data': {'object': [
            'foo', 'bar', {'child': True}, 'baz'
        ]}
    }

    result = chevron2.render(**args)
    expected = 'foobarbaz'

    assert result == expected

def test_closing_tag_only():
    args = {
        'template': '{{ foo } bar',
        'data': {'foo': 'xx'}
    }

    with pytest.raises(chevron2.ChevronError):
        chevron2.render(**args)

def test_current_line_rest():
    args = {
        'template': 'first line\nsecond line\n {{ foo } bar',
        'data': {'foo': 'xx'}
    }

    with pytest.raises(chevron2.ChevronError):
        chevron2.render(**args)

def test_no_opening_tag():
    args = {
        'template': 'oops, no opening tag {{/ closing_tag }}',
        'data': {'foo': 'xx'}
    }

    with pytest.raises(chevron2.ChevronError):
        chevron2.render(**args)

# https://github.com/noahmorrison/chevron2/issues/17
def test_callable_1():
    args_passed = {}

    def first(content, render):
        args_passed['content'] = content
        args_passed['render'] = render

        return "not implemented"

    args = {
        'template': '{{{postcode}}} {{#first}} {{{city}}} || {{{town}}} '
                    '|| {{{village}}} || {{{state}}} {{/first}}',
        'data': {
            "postcode": "1234",
            "city": "Mustache City",
            "state": "Nowhere",
            "first": first,
        }

    }

    result = chevron2.render(**args)
    expected = '1234 not implemented'
    template_content = " {{& city }} || {{& town }} || {{& village }} "\
                        "|| {{& state }} "

    assert result == expected
    assert args_passed['content'] == template_content

def test_callable_2():

    def first(content, render):
        result = render(content)
        result = [x.strip() for x in result.split(" || ") if x.strip()]
        return result[0]

    args = {
        'template': '{{{postcode}}} {{#first}} {{{city}}} || {{{town}}} '
                    '|| {{{village}}} || {{{state}}} {{/first}}',
        'data': {
            "postcode": "1234",
            "town": "Mustache Town",
            "state": "Nowhere",
            "first": first,
        }
    }

    result = chevron2.render(**args)
    expected = '1234 Mustache Town'

    assert result == expected

def test_callable_3():
    '''Test generating some data within the function
    '''

    def first(content, render):
        result = render(content, {'city': "Injected City"})
        result = [x.strip() for x in result.split(" || ") if x.strip()]
        return result[0]

    args = {
        'template': '{{{postcode}}} {{#first}} {{{city}}} || {{{town}}} '
                    '|| {{{village}}} || {{{state}}} {{/first}}',
        'data': {
            "postcode": "1234",
            "town": "Mustache Town",
            "state": "Nowhere",
            "first": first,
        }
    }

    result = chevron2.render(**args)
    expected = '1234 Injected City'

    assert result == expected

def test_callable_4():
    '''Test render of partial inside lambda
    '''

    def function(content, render):
        return render(content)

    args = {
        'template': '{{#function}}{{>partial}}{{!comment}}{{/function}}',
        'partials_dict': {
            'partial': 'partial content',
        },
        'data': {
            'function': function,
        }
    }

    result = chevron2.render(**args)
    expected = 'partial content'

    assert result == expected


# https://github.com/noahmorrison/chevron/issues/39
def test_nest_loops_with_same_key():
    args = {
        'template': 'A{{#x}}B{{#x}}{{.}}{{/x}}C{{/x}}D',
        'data': {'x': ['z', 'x']}
    }

    result = chevron2.render(**args)
    expected = 'ABzxCBzxCD'

    assert result == expected

# https://github.com/noahmorrison/chevron/issues/49
def test_partial_indentation():
    args = {
        'template': '\t{{> count }}',
        'partials_dict': {
            'count': '\tone\n\ttwo'
        }
    }

    result = chevron2.render(**args)
    expected = '\t\tone\n\t\ttwo'

    assert result == expected

# https://github.com/noahmorrison/chevron/issues/52
def test_indexed():
    args = {
        'template': 'count {{count.0}}, {{count.1}}, '
                    '{{count.100}}, {{nope.0}}',
        'data': {
            "count": [5, 4, 3, 2, 1],
        }
    }

    result = chevron2.render(**args)
    expected = 'count 5, 4, , '

    assert result == expected

def test_iterator_scope_indentation():
    args = {
        'data': {
            'thing': ['foo', 'bar', 'baz'],
        },
        'template': '{{> count }}',
        'partials_dict': {
            'count': '    {{> iter_scope }}',
            'iter_scope': 'foobar\n{{#thing}}\n {{.}}\n{{/thing}}'
        }
    }

    result = chevron2.render(**args)
    expected = '    foobar\n     foo\n     bar\n     baz\n'

    assert result == expected

# https://github.com/noahmorrison/chevron/pull/73
def test_namedtuple_data():
    NT = collections.namedtuple('NT', ['foo', 'bar'])
    args = {
        'template': '{{foo}} {{bar}}',
        'data': NT('hello', 'world')
    }

    result = chevron2.render(**args)
    expected = 'hello world'

    assert result == expected

def test_get_key_not_in_dunder_dict_returns_attribute():
    class C:
        foo = "bar"

    instance = C()
    assert "foo" not in instance.__dict__

    args = {
        'template': '{{foo}}',
        'data': instance
    }
    result = chevron2.render(**args)
    expected = 'bar'

    assert result == expected

# https://github.com/noahmorrison/chevron/pull/94
def test_keep():
    args = {
        'template': '{{ first }} {{ second }} {{ third }}',
        'data': {
            "first": "1st",
            "third": "3rd",
        },
    }

    result = chevron2.render(**args)
    expected = '1st  3rd'
    assert result == expected

    args['keep'] = True

    result = chevron2.render(**args)
    expected = '1st {{ second }} 3rd'
    assert result == expected

    args['template'] = '{{first}} {{second}} {{third}}'
    result = chevron2.render(**args)
    expected = '1st {{ second }} 3rd'
    assert result == expected

    args['template'] = '{{   first    }} {{    second    }} {{    third   }}'
    result = chevron2.render(**args)
    expected = '1st {{ second }} 3rd'
    assert result == expected

# https://github.com/noahmorrison/chevron/pull/94
def test_keep_from_partials():
    args = {
        'template': '{{ first }} {{> with_missing_key }} {{ third }}',
        'data': {
            "first": "1st",
            "third": "3rd",
        },
        'partials_dict': {
            'with_missing_key': '{{missing_key}}',
        },
    }

    result = chevron2.render(**args)
    expected = '1st  3rd'
    assert result == expected

    args['keep'] = True

    result = chevron2.render(**args)
    expected = '1st {{ missing_key }} 3rd'
    assert result == expected
