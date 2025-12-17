# mystace - A fast, pure Python {{mustache}} renderer

[![PyPI version](https://badge.fury.io/py/mystace.svg)](https://badge.fury.io/py/mystace)
[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)
[![tests](https://github.com/eliotwrobson/mystace/actions/workflows/tests.yml/badge.svg)](https://github.com/eliotwrobson/mystace/actions/workflows/tests.yml)
[![lint](https://github.com/eliotwrobson/mystace/actions/workflows/lint-python.yml/badge.svg)](https://github.com/eliotwrobson/mystace/actions/workflows/lint-python.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)

A fast, spec-compliant Python implementation of the [{{mustache}}](http://mustache.github.io) templating language. A spiritual successor to [chevron](https://github.com/noahmorrison/chevron), optimized for performance through caching and efficient rendering.

## Why mystace?

### mystace is fast

Mystace outperforms all other pure Python mustache implementations through its cached rendering approach. Pre-parsing templates into an optimized tree structure means subsequent renders are extremely fast. Included [microbenchmarks](https://github.com/eliotwrobson/mystace/actions/workflows/tests.yml) demonstrate significant performance advantages, particularly for repeated renders of the same template.

### mystace is fully spec compliant

Mystace passes **all 163 required tests** from the official [{{mustache}} spec](https://github.com/mustache/spec) v1.4, providing complete support for:

- Variables (escaped and unescaped)
- Sections (normal and inverted)
- Partials with proper indentation handling
- Comments
- **Delimiter changes** (e.g., `{{=<% %>=}}`)

The 66 skipped tests are for **optional features** not in the core spec:

- Lambda functions (`~lambdas.json` - 22 tests)
- Dynamic partial names (`~dynamic-names.json` - 22 tests)
- Template inheritance (`~inheritance.json` - 34 tests)

These optional modules (prefixed with `~` in the spec) may be implemented in future versions. To see detailed test results, check [the spec test file](https://github.com/eliotwrobson/mystace/blob/main/tests/test_specs.py).

## Installation

```bash
pip install mystace
```

Requires Python 3.10 or higher.

## Usage

### Basic rendering

```python
import mystace

# Simple variable substitution
result = mystace.render_from_template(
    'Hello, {{ name }}!',
    {'name': 'World'}
)
# Output: 'Hello, World!'
```

### Cached rendering (recommended for repeated use)

For templates you'll render multiple times, use `MustacheRenderer` to cache the parsed template:

```python
import mystace

# Parse template once
renderer = mystace.MustacheRenderer.from_template('Hello, {{ name }}!')

# Render multiple times with different data
print(renderer.render({'name': 'World'}))  # Hello, World!
print(renderer.render({'name': 'Alice'}))  # Hello, Alice!
print(renderer.render({'name': 'Bob'}))    # Hello, Bob!
```

### Sections

```python
import mystace

template = '''
{{#users}}
  - {{ name }} ({{ email }})
{{/users}}
'''

data = {
    'users': [
        {'name': 'Alice', 'email': 'alice@example.com'},
        {'name': 'Bob', 'email': 'bob@example.com'}
    ]
}

result = mystace.render_from_template(template, data)
# Output:
#   - Alice (alice@example.com)
#   - Bob (bob@example.com)
```

### Inverted sections

```python
import mystace

template = '{{^items}}No items found.{{/items}}'

# With empty list
result = mystace.render_from_template(template, {'items': []})
# Output: 'No items found.'

# With items
result = mystace.render_from_template(template, {'items': [1, 2, 3]})
# Output: ''
```

### Partials

```python
import mystace

template = '{{>header}}Content here{{>footer}}'

partials = {
    'header': '<header>{{title}}</header>',
    'footer': '<footer>© 2025</footer>'
}

result = mystace.render_from_template(
    template,
    {'title': 'My Page'},
    partials=partials
)
# Output: '<header>My Page</header>Content here<footer>© 2025</footer>'
```

### Delimiter changes

```python
import mystace

# Change delimiters to avoid conflicts
template = '''
{{=<% %>=}}
<script>
  const data = <% data %>;
</script>
'''

result = mystace.render_from_template(template, {'data': '{"key": "value"}'})
# Output:
# <script>
#   const data = {"key": "value"};
# </script>
```

### Custom escaping and stringification

```python
import mystace

# Custom HTML escaping
def my_escape(text):
    return text.replace('&', '&amp;').replace('<', '&lt;')

result = mystace.render_from_template(
    '{{ html }}',
    {'html': '<div>Hello</div>'},
    html_escape_fn=my_escape
)

# Custom stringification for non-string values
def my_stringify(value):
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)

result = mystace.render_from_template(
    'Value: {{ flag }}',
    {'flag': True},
    stringify=my_stringify
)
# Output: 'Value: true'
```

## Development

This project uses [uv](https://github.com/astral-sh/uv) for dependency management:

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest tests/

# Run tests with coverage
uv run pytest tests/ --cov=src/mystace --cov-report=term --ignore=tests/test_speed.py

# Run benchmarks (Python 3.14 only)
uv run pytest tests/test_speed.py --benchmark-only

# Format code
uv run ruff format

# Type checking
uv run mypy src/
```

## Performance

Mystace is designed for speed through:

- **Pre-parsed templates**: Parse once, render many times with `MustacheRenderer`
- **Efficient tree structure**: Optimized internal representation
- **Minimal overhead**: Pure Python with no unnecessary allocations

Benchmark results show mystace as the fastest pure Python mustache implementation, particularly excelling at repeated renders of the same template.

## Contributing

Contributions are welcome! Areas for improvement:

- Lambda function support
- Dynamic partial names
- Template inheritance
- Additional optimization

## TODO

- Implement remaining spec features (lambdas, dynamic names, inheritance)
- Further performance optimizations
- Additional documentation and examples
