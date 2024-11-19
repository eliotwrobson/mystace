from typing import Any

LAMBDA = "<lambda>"


def html_escape(s: str) -> str:
    s = s.replace("&", "&amp;")  # Must be done first!
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace('"', "&quot;")
    return s


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
