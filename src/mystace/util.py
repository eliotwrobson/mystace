from typing import Any

LAMBDA = "<lambda>"

# Pre-build translation table for HTML escaping (much faster than multiple replace calls)
_HTML_ESCAPE_TABLE = str.maketrans(
    {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
    }
)


def html_escape(s: str) -> str:
    return s.translate(_HTML_ESCAPE_TABLE)


def is_whitespace(string: str) -> bool:
    # ''.isspace() returns False
    # for our purposes if there is nothing after or behind the tag
    # it still should count as whitespace and the tag should be standalone
    return not string or string.isspace()


def is_callable(val) -> bool:
    # isinstance for collections.abc if too slow
    return hasattr(val, "__call__")


def to_str(val: Any) -> str:
    # basic str(...) but with None accounted
    if val is None:
        return ""
    return str(val)
