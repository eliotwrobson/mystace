# mystace

[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)
[![tests](https://github.com/eliotwrobson/chevron2/actions/workflows/tests.yml/badge.svg)](https://github.com/eliotwrobson/chevron2/actions/workflows/tests.yml)
[![lint](https://github.com/eliotwrobson/chevron2/actions/workflows/lint-python.yml/badge.svg)](https://github.com/eliotwrobson/chevron2/actions/workflows/lint-python.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)

A Python implementation of the [{{mustache}}](http://mustache.github.io) templating language. It's compliant with
the [specifications](https://github.com/mustache/spec) up to v1.4.1.

Why chevron2?
------------

I'm glad you asked!

### chevron2 is fast ###

Included microbenchmarks show mystace heavily outperforming all other libraries tested.

### chevron is pep8 ###

The flake8 command is run by [travis](https://travis-ci.org/noahmorrison/chevron) to ensure consistency.

### chevron is spec compliant ###

Chevron passes all the unittests provided by the [spec](https://github.com/mustache/spec) (in every version listed below).

If you find a test that chevron does not pass, please [report it.](https://github.com/noahmorrison/chevron/issues/new)




USAGE
-----

Commandline usage: (if installed via pypi)
```
usage: chevron [-h] [-v] [-d DATA] [-p PARTIALS_PATH] [-e PARTIALS_EXT]
               [-l DEF_LDEL] [-r DEF_RDEL]
               template

positional arguments:
  template              The mustache file

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -d DATA, --data DATA  The json data file
  -p PARTIALS_PATH, --path PARTIALS_PATH
                        The directory where your partials reside
  -e PARTIALS_EXT, --ext PARTIALS_EXT
                        The extension for your mustache partials, 'mustache'
                        by default
  -l DEF_LDEL, --left-delimiter DEF_LDEL
                        The default left delimiter, "{{" by default.
  -r DEF_RDEL, --right-delimiter DEF_RDEL
                        The default right delimiter, "}}" by default.
```

Python usage with strings
```python
import chevron

chevron.render('Hello, {{ mustache }}!', {'mustache': 'World'})
```

Python usage with file
```python
import chevron

with open('file.mustache', 'r') as f:
    chevron.render(f, {'mustache': 'World'})
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

chevron supports partials (via dictionaries)
```python
import chevron

args = {
    'template': 'Hello, {{> thing }}!',

    'partials': {
        'thing': 'World'
    }
}

chevron.render(**args)
```

chevron supports partials (via the filesystem)
```python
import chevron

args = {
    'template': 'Hello, {{> thing }}!',

    # defaults to .
    'partials_path': 'partials/',

    # defaults to mustache
    'partials_ext': 'ms',
}

# ./partials/thing.ms will be read and rendered
chevron.render(**args)
```

chevron supports lambdas
```python
import chevron

def first(text, render):
    # return only first occurance of items
    result = render(text)
    return [ x.strip() for x in result.split(" || ") if x.strip() ][0]

def inject_x(text, render):
    # inject data into scope
    return render(text, {'x': 'data'})

args = {
    'template': 'Hello, {{# first}} {{x}} || {{y}} || {{z}} {{/ first}}!  {{# inject_x}} {{x}} {{/ inject_x}}',

    'data': {
        'y': 'foo',
        'z': 'bar',
        'first': first,
        'inject_x': inject_x
    }
}

chevron.render(**args)
```

INSTALL
-------

- with git
```
$ git clone https://github.com/noahmorrison/chevron.git
```

or using submodules
```
$ git submodules add https://github.com/noahmorrison/chevron.git
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
