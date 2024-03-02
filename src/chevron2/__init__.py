"""
Mustache v1.4 implementation with lambdas.

Usable both in code and as CLI.
To render a mustache template use `combustache.render`.
Processed templates are cached; to clear cache use `combustache.cache_clear`.

Typical usage in code: ::

    >>> import combustache
    >>> template = 'Hello my name is {{>fancy_name}}!'
    >>> partials = {'fancy_name': '-> {{name}} <-'}
    >>> data = {'name': 'Anahit'}
    >>> combustache.render(template, data, partials)
    'Hello my name is -> Anahit <-!'

Typical usage as CLI: ::

    $ curl https://end.point/v1/api | combustache template.txt -o out.txt
    $ cat out.txt
    Hello world!
"""

from chevron2.exceptions import (
    Chevron2Error,
    DelimiterError,
    MissingClosingTagError,
    StrayClosingTagError,
)
from chevron2.main import cache_clear, render
from chevron2.mustache_tree import create_mustache_tree
from chevron2.tokenize import tokenize

__all__ = [
    "render",
    "cache_clear",
    "tokenize",
    "Chevron2Error",
    "DelimiterError",
    "MissingClosingTagError",
    "StrayClosingTagError",
    "create_mustache_tree",
]
