from __future__ import annotations

import enum
import typing as t
from collections import deque

from typing_extensions import assert_never

from .tokenize import tokenize

# be returned
ContextObjT = t.Any


class ContextStack:
    context: t.List[ContextObjT]

    def __init__(self, context: t.Optional[t.List[ContextObjT]] = None) -> None:
        if context is None:
            self.context = []
        else:
            self.context = context

    def get(self, key: str) -> t.Any:
        if key == ".":
            return self[-1]

        chain = key.split(".")
        reversed_ctx = reversed(self)

        found = None
        for item in reversed_ctx:
            found = deep_get(item, chain[0])
            if found is not None:
                break

        if found is None:
            return None

        for key in chain[1:]:
            found = deep_get(found, key)
        return found


def deep_get(item: t.Any, key: str) -> t.Any:
    try:
        item = item()
    except TypeError:
        pass

    try:
        try:
            return item[key]
        except KeyError:
            return None
    except TypeError:
        pass

    try:
        idx = int(key)
        try:
            return item[idx]
        except IndexError:
            return None
    except ValueError:
        pass

    return getattr(item, key, None)


### TODO probably need to refactor the above

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
    VARIABLE = 6
    VARIABLE_RAW = 7


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

    def recursive_display(self) -> str:
        res_str = self.__repr__() + "\n"

        for child in self.children:
            res_str += "    " + child.recursive_display() + "\n"

        return res_str

    def __repr__(self) -> str:
        if self.data:
            return f"<{self.__class__.__name__}: {self.tag_type}, {self.data!r}>"
        return f"<{self.__class__.__name__}: {self.tag_type}>"


class MustacheRenderer:
    mustache_tree: MustacheTreeNode

    def __init__(self, mustache_tree: MustacheTreeNode) -> None:
        assert mustache_tree.tag_type is TagType.ROOT
        self.mustache_tree = mustache_tree

    def render(self, context: ContextObjT) -> str:
        res_list = []
        starting_context = ContextStack([context])
        work_deque: t.Deque[t.Tuple[MustacheTreeNode, ContextStack]] = deque(
            [(self.mustache_tree, starting_context)]
        )

        while work_deque:
            curr_node, curr_context = work_deque.popleft()

            if curr_node.tag_type is TagType.LITERAL:
                res_list.append(curr_node.data)
            elif curr_node.tag_type is

        return "".join(res_list)


def create_mustache_tree(thing: str) -> MustacheTreeNode:
    # TODO make a special tag type for the root? Unsure
    root = MustacheTreeNode(
        TagType.ROOT,
        "",
    )
    work_stack: t.Deque[MustacheTreeNode] = deque([root])

    for token_type, token_data in tokenize(thing):
        print(work_stack)

        if token_type == "literal":
            literal_node = MustacheTreeNode(TagType.LITERAL, token_data)
            work_stack[-1].children.append(literal_node)
            print("lit:", token_data)
        elif token_type in {"section", "inverted section"}:
            tag_type = (
                TagType.SECTION if token_type == "section" else TagType.INVERTED_SECTION
            )
            section_node = MustacheTreeNode(tag_type, token_data)
            # Add section to list of children
            work_stack[-1].children.append(section_node)

            # Add section to work stack and descend in on the next iteration.
            work_stack.append(section_node)
            print("sec:", tag_type, token_data)
        elif token_type == "end":
            assert work_stack[-1].data == token_data
            # Close the current section by popping off the end of the work stack.
            work_stack.pop()
            print("end:", token_data)
        elif token_type in {"variable", "no escape"}:
            tag_type = (
                TagType.VARIABLE if token_type == "variable" else TagType.VARIABLE_RAW
            )
            variable_node = MustacheTreeNode(tag_type, token_data)
            # Add section to list of children
            work_stack[-1].children.append(variable_node)
        else:
            print(token_type, token_data)
            assert_never(token_type)

    return root


# def render_from