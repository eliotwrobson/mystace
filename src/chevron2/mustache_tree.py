from __future__ import annotations

import enum
import typing as t
from collections import deque

from typing_extensions import assert_never

from .tokenize import tokenize

# '!': 'comment',
# '#': 'section',
# '^': 'inverted section',
# '/': 'end',
# '>': 'partial',
# '=': 'set delimiter?',
# '{': 'no escape?',
# '&': 'no escape'


class TagType(enum.Enum):
    ROOT = -1
    LITERAL = 0
    COMMENT = 1
    SECTION = 2
    INVERTED_SECTION = 3
    END_SECTION = 4
    PARTIAL = 5


class MustacheTreeNode:
    __slots__ = ("tag_type", "data", "children")

    tag_type: TagType
    data: str
    children: t.Optional[t.List[MustacheTreeNode]]

    def __init__(
        self,
        tag_type: TagType,
        data: str,
    ) -> None:
        self.tag_type = tag_type
        self.data = data
        self.children = []


def create_mustache_tree(thing: str) -> MustacheTreeNode:
    # TODO make a special tag type for the root? Unsure
    root = MustacheTreeNode(
        TagType.ROOT,
        "",
    )
    work_stack: t.Deque[MustacheTreeNode] = deque([root])

    for token_type, token_data in tokenize(thing):
        if token_type == "literal":
            work_stack[-1].children
            print("lit:", token_data)
        elif token_type == "section":
            print("sec:", token_data)
        elif token_type == "inverted section":
            print("sec:", token_data)
        elif token_type == "end":
            print("end:", token_data)
        else:
            assert_never(token_type)
