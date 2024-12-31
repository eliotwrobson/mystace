
# mystace - A fast, pure Python {{mustache}} renderer

[![PyPI version](https://badge.fury.io/py/mystace.svg)](https://badge.fury.io/py/mystace)
[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)
[![tests](https://github.com/eliotwrobson/mystace/actions/workflows/tests.yml/badge.svg)](https://github.com/eliotwrobson/mystace/actions/workflows/tests.yml)
[![lint](https://github.com/eliotwrobson/mystace/actions/workflows/lint-python.yml/badge.svg)](https://github.com/eliotwrobson/mystace/actions/workflows/lint-python.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)

A Python implementation of the [{{mustache}}](http://mustache.github.io) templating language.
Still a _work in progress_, but core rendering features are working (issues are with partials and delimiter
swap). A spiritual successor to [chevron](https://github.com/noahmorrison/chevron).

Why mystace?
------------

I'm glad you asked!

### mystace is fast ###

Included microbenchmarks show mystace heavily outperforming all other libraries tested.

### mystace is *almost* spec compliant ###

Mystace passes nearly all the unit provided by the [{{mustache}} spec](https://github.com/mustache/spec).
To see which tests are currently not passing, see [the spec test file](https://github.com/eliotwrobson/mystace/blob/main/tests/test_specs.py).
They are only

Project status
------------
Currently a work in progress. The core rendering logic is solid, but still working out bugs with a few
test cases. If there is community interest and people will find this useful, I will find time to get
the rest of test cases working. As is, I am happy to review pull requests and write test cases.

Usage
-----

Python usage with strings
```python
import mystace

mystace.render('Hello, {{ mustache }}!', {'mustache': 'World'})
```

Python usage with data structure
```python
import mystace

template_str = 'Hello, {{ mustache }}!'
template_renderer = mystace.MustacheRenderer.from_template(template_str)

template_renderer.render({'mustache': 'World'})

template_renderer.render({'mustache': 'Dave'})
```

Install
-------
```
$ pip install mystace
```

TODO
---
* get fully spec compliant
* get popular
* have people complain
* fix those complaints
