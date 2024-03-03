from __future__ import annotations

import copy
import enum
import typing as t
from collections import deque

import typing_extensions as te

from .tokenize import tokenize
from .util import html_escape

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
            return self.context[-1]

        chain = key.split(".")
        reversed_ctx = reversed(self.context)

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

    def copy(self) -> ContextStack:
        new_context = copy.copy(self.context)
        return ContextStack(new_context)

    def open_section(self, key: str) -> t.List[ContextStack]:
        new_context = self.get(key)

        # If lookup is "falsy", no need to open the section or copy
        # new context
        if not new_context:
            return []

        # In the case of the list, need a new context for each item
        if isinstance(new_context, list):
            res_list = []

            for item in new_context:
                new_stack = self.copy()
                new_stack.context.append(item)
                res_list.append(new_stack)

            return res_list

        new_stack = self.copy()
        new_stack.context.append(new_context)
        return [new_stack]


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

        # Never need to read the root because it has no data
        work_deque: t.Deque[t.Tuple[MustacheTreeNode, ContextStack]] = deque(
            (node, starting_context) for node in self.mustache_tree.children
        )
        # print(context)
        while work_deque:
            curr_node, curr_context = work_deque.popleft()
            # print(curr_node.tag_type)
            if curr_node.tag_type is TagType.LITERAL:
                res_list.append(curr_node.data)
            elif curr_node.tag_type is TagType.VARIABLE:
                variable_content = curr_context.get(curr_node.data)
                print(curr_node.data, variable_content)
                if variable_content:
                    res_list.append(html_escape(str(variable_content)))
            elif curr_node.tag_type is TagType.VARIABLE_RAW:
                variable_content = curr_context.get(curr_node.data)
                if variable_content:
                    res_list.append(str(variable_content))
            elif curr_node.tag_type is TagType.SECTION:
                new_context_stacks = curr_context.open_section(curr_node.data)

                for new_context_stack in reversed(new_context_stacks):
                    for child_node in reversed(curr_node.children):
                        # No need to make a copy of the context per-child, it's immutable
                        work_deque.appendleft((child_node, new_context_stack))

            elif curr_node.tag_type is TagType.INVERTED_SECTION:
                # No need to add to the context stack, inverted sections
                # by definition aren't in the namespace and can't add anything.
                lookup_data = curr_context.get(curr_node.data)

                if not bool(lookup_data):
                    for child_node in reversed(curr_node.children):
                        work_deque.appendleft((child_node, curr_context))

        return "".join(res_list)

    @classmethod
    def from_template(cls: te.Self, template_str: str) -> te.Self:
        return cls(create_mustache_tree(template_str))


def create_mustache_tree(thing: str) -> MustacheTreeNode:
    # TODO make a special tag type for the root? Unsure
    root = MustacheTreeNode(
        TagType.ROOT,
        "",
    )
    work_stack: t.Deque[MustacheTreeNode] = deque([root])

    for token_type, token_data in tokenize(thing):
        # print(work_stack)

        if token_type == "literal":
            literal_node = MustacheTreeNode(TagType.LITERAL, token_data)
            work_stack[-1].children.append(literal_node)
            # print("lit:", token_data)
        elif token_type in {"section", "inverted section"}:
            tag_type = (
                TagType.SECTION if token_type == "section" else TagType.INVERTED_SECTION
            )
            section_node = MustacheTreeNode(tag_type, token_data)
            # Add section to list of children
            work_stack[-1].children.append(section_node)

            # Add section to work stack and descend in on the next iteration.
            work_stack.append(section_node)
            # print("sec:", tag_type, token_data)
        elif token_type == "end":
            assert work_stack[-1].data == token_data
            # Close the current section by popping off the end of the work stack.
            work_stack.pop()
            # print("end:", token_data)
        elif token_type in {"variable", "no escape"}:
            tag_type = (
                TagType.VARIABLE if token_type == "variable" else TagType.VARIABLE_RAW
            )
            variable_node = MustacheTreeNode(tag_type, token_data)
            # Add section to list of children
            work_stack[-1].children.append(variable_node)
        else:
            # print(token_type, token_data)
            # assert_never(token_type)
            raise Exception

    return root


def render_from_template(template: str, context: ContextObjT, partials=None) -> str:
    return MustacheRenderer.from_template(template).render(context)
