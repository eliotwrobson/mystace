"""
Mustache v1.4 implementation.

To render a mustache template use `mystace.render_from_template`.
Processed templates are cached via `MustacheRenderer.from_template`.

Typical usage: ::

    >>> import mystace
    >>> template = 'Hello my name is {{>fancy_name}}!'
    >>> partials = {'fancy_name': '-> {{name}} <-'}
    >>> data = {'name': 'Anahit'}
    >>> mystace.render_from_template(template, data, partials)
    'Hello my name is -> Anahit <-!'
"""

from mystace.exceptions import (
    DelimiterError,
    MissingClosingTagError,
    MystaceError,
    StrayClosingTagError,
)
from mystace.mustache_tree import (
    MustacheRenderer,
    create_mustache_tree,
    render_from_template,
)
from mystace.tokenize import mustache_tokenizer

__all__ = [
    "MystaceError",
    "DelimiterError",
    "MissingClosingTagError",
    "StrayClosingTagError",
    "create_mustache_tree",
    "render_from_template",
    "MustacheRenderer",
    "mustache_tokenizer",
]
