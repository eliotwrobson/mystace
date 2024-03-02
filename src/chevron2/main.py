import functools
import html
import typing as t

from chevron2.ctx import Ctx
from chevron2.nodes.comment import Comment
from chevron2.nodes.delimiter import Delimiter
from chevron2.nodes.interpolation import Ampersand, Interpolation, Triple
from chevron2.nodes.node import Node
from chevron2.nodes.partial import Partial
from chevron2.nodes.section import Closing, Inverted, Section
from chevron2.util import to_str

_nodes: set[type[Node]] = {
    Comment,
    Section,
    Ampersand,
    Inverted,
    Closing,
    Triple,
    Partial,
    Delimiter,
}
_node_types = {node.left: node for node in _nodes}
_left_to_right = {node.left: node.right for node in _nodes}


def create_node(
    content: str,
    tag_start: int,
    tag_end: int,
    template: str,
    template_start: int,
    template_end: int,
    left_delimiter: str,
    right_delimiter: str,
) -> Node:
    kwargs = {
        "content": content,
        "tag_start": tag_start,
        "tag_end": tag_end,
        "template": template,
        "template_start": template_start,
        "template_end": template_end,
        "left_delimiter": left_delimiter,
        "right_delimiter": right_delimiter,
    }
    # so we dont index into an empty string
    # it will be stripped into an empty string anyway
    if not content:
        content = " "
    # find_node function here is already dealing with the right character of
    # Triple and Delimiter
    node_type = _node_types.get(content[0], Interpolation)
    return node_type(**kwargs)


def find_node(
    template: str,
    search_start: int,
    template_end: int,
    left_delimiter: str,
    right_delimiter: str,
) -> t.Optional[t.Tuple[str, int, int]]:
    start_idx = template.find(left_delimiter, search_start, template_end)
    if start_idx < search_start:
        return None

    left_idx = start_idx + len(left_delimiter)
    if left_idx >= template_end:
        return None

    right = _left_to_right.get(template[left_idx], "")
    new_delimiter = right + right_delimiter
    to_add = len(right)

    right_idx = template.find(new_delimiter, left_idx, template_end)
    if right_idx < left_idx:
        return None

    end_idx = right_idx + len(new_delimiter)
    content = template[left_idx : right_idx + to_add]
    return content, start_idx, end_idx


@functools.cache
def parse(
    template: str,
    template_start: int,
    template_end: int,
    left_delimiter: str = "{{",
    right_delimiter: str = "}}",
) -> t.List[t.Union[Node, str]]:
    nodes = []
    search_start = template_start
    while True:
        node_info = find_node(
            template,
            search_start,
            template_end,
            left_delimiter,
            right_delimiter,
        )

        if node_info is None:
            nodes.append(template[search_start:template_end])
            break

        content, start, end = node_info
        node = create_node(
            content,
            start,
            end,
            template,
            template_start,
            template_end,
            left_delimiter,
            right_delimiter,
        )

        if isinstance(node, Delimiter):
            left_delimiter = node.left_delimiter
            right_delimiter = node.right_delimiter

        nodes.append(template[search_start : node.start])
        if not node.ignorable:
            nodes.append(node)
        search_start = node.parse_end
    return nodes


def _render(
    template: str,
    ctx: Ctx,
    partials: dict,
    opts: dict,
    left_delimiter: str = "{{",
    right_delimiter: str = "}}",
) -> str:
    root = parse(template, 0, len(template), left_delimiter, right_delimiter)
    return "".join(
        [
            node.handle(ctx, partials, opts) if isinstance(node, Node) else node
            for node in root
        ]
    )


def render(
    template: str,
    data: t.Optional[t.Dict] = None,
    partials: t.Optional[t.Dict[str, str]] = None,
    left_delimiter: str = "{{",
    right_delimiter: str = "}}",
    *,
    stringify: t.Callable[[t.Any], str] = to_str,
    escape: t.Callable[[str], str] = html.escape,
    missing_data: t.Callable[[], t.Any] = lambda: "",
) -> str:
    """
    Renders a mustache template.

    Args:
        template: Mustache template.
        data: Values to insert into the template.
        partials: Partials to insert into the template.
        left_delimiter: Left tag delimiter.
        right_delimiter: Right tag delimiter.

    Keyword args:
        stringify: String conversion function.
        escape: Escaping function.
        missing_data: Function called on missing data.

    Returns:
        A rendered template.

    Raises:
        DelimiterError: Bad delimiter tag.
        MissingClosingTagError: Missing closing tag.
        StrayClosingTagError: Stray closing tag.
    """
    if data is None:
        data = {}

    opts = {
        "stringify": stringify,
        "escape": escape,
        "missing_data": missing_data,
    }
    if partials is None:
        partials = {}
    ctx = Ctx([data])
    return _render(template, ctx, partials, opts, left_delimiter, right_delimiter)


def cache_clear():
    """
    Clears cached templates.
    """
    parse.cache_clear()
