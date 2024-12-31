
# mystace - A fast, pure Python {{mustache}} renderer

[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)
[![tests](https://github.com/eliotwrobson/mystace/actions/workflows/tests.yml/badge.svg)](https://github.com/eliotwrobson/mystace/actions/workflows/tests.yml)
[![lint](https://github.com/eliotwrobson/mystace/actions/workflows/lint-python.yml/badge.svg)](https://github.com/eliotwrobson/mystace/actions/workflows/lint-python.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)

A Python implementation of the [{{mustache}}](http://mustache.github.io) templating language. It's compliant with
the [specifications](https://github.com/mustache/spec) up to v1.4.1.

Why mystace?
------------

I'm glad you asked!

### mystace is fast ###

Included microbenchmarks show mystace heavily outperforming all other libraries tested.

### chevron is *almost* spec compliant ###

Chevron passes nearly all the unit provided by the [spec](https://github.com/mustache/spec) (in every version listed below).

If you find a test that chevron does not pass, please [report it.](https://github.com/noahmorrison/chevron/issues/new)




USAGE
-----

Python usage with strings
```python
import mystace

mystace.render('Hello, {{ mustache }}!', {'mustache': 'World'})
```

Python usage with unpacking
```python
import chevron

args = {
  'template': 'Hello, {{ mustache }}!',

  'data': {
    'mustache': 'World'
  }
}

chevron.render(**args)
```

INSTALL
-------

- with git
```
$ git clone https://github.com/eliotwrobson/mystace.git
```

or using submodules
```
$ git submodules add https://github.com/eliotwrobson/mystace.git
```

Also available on pypi!

- with pip
```
$ pip install chevron
```



TODO
---

* get popular
* have people complain
* fix those complaints
