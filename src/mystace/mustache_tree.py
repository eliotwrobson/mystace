from __future__ import annotations

import enum
import typing as t
from collections import deque

import typing_extensions as te

from .exceptions import (
    MissingClosingTagError,
    MystaceError,
    NodeHasNoChildren,
    StrayClosingTagError,
)
from .tokenize import TokenTuple, TokenType, mustache_tokenizer
from .util import html_escape

# be returned
ContextObjT = t.Any

# Tokens that can appear standalone on a line (for whitespace removal)
_STANDALONE_TOKENS = (
    TokenType.COMMENT,
    TokenType.END_SECTION,
    TokenType.INVERTED_SECTION,
    TokenType.SECTION,
    TokenType.PARTIAL,
    TokenType.DELIMITER,
)


class ContextNode:
    __slots__ = ("context", "parent_context_node")

    context: ContextObjT
    parent_context_node: t.Optional[ContextNode]

    def __init__(
        self,
        context: ContextObjT,
        parent_context_node: t.Optional[ContextNode] = None,
    ) -> None:
        self.context = context
        self.parent_context_node = parent_context_node

    def get(self, key: str) -> t.Any:
        if key == ".":
            return self.context

        chain_iter = iter(key.split("."))
        curr_ctx = self.context
        parent_node = self.parent_context_node

        first_key = next(chain_iter)

        # TODO I think this is where changes need to be made if we want to
        # support indexing and lambdas.
        outer_context = None

        while curr_ctx is not None:
            if isinstance(curr_ctx, dict) and first_key in curr_ctx:
                outer_context = curr_ctx[first_key]
                break
            else:
                if parent_node is None:
                    curr_ctx = None
                else:
                    curr_ctx = parent_node.context
                    parent_node = parent_node.parent_context_node

        if outer_context is None:
            return None

        # Loop through the rest
        for key in chain_iter:
            if isinstance(outer_context, list):
                try:
                    int_key = int(key)
                    outer_context = outer_context[int_key]
                except Exception:
                    return None

            elif isinstance(outer_context, dict) and key in outer_context:
                outer_context = outer_context[key]
            else:
                return None

        return outer_context

    def open_section(self, key: str) -> t.List[ContextNode]:
        new_context = self.get(key)

        # If lookup is "falsy", no need to open the section or copy
        # new context
        if not new_context:
            return []

        # In the case of the list, need a new context for each item
        if isinstance(new_context, list):
            res_list = []

            for item in new_context:
                new_stack = ContextNode(item, self)
                # new_stack.parent_context_node = self
                res_list.append(new_stack)

            return res_list

        new_stack = ContextNode(new_context, self)
        return [new_stack]


class TagType(enum.Enum):
    """
    Types of tags that can appear in a tree,
    different from the kinds that can appear in general.
    """

    ROOT = -1
    LITERAL = 0
    SECTION = 2
    INVERTED_SECTION = 3
    PARTIAL = 5
    VARIABLE = 6
    VARIABLE_RAW = 7


class MustacheTreeNode:
    __slots__ = ("tag_type", "data", "children", "offset")

    tag_type: TagType
    data: str
    children: t.Optional[t.List[MustacheTreeNode]]
    offset: int

    def __init__(
        self,
        tag_type: TagType,
        data: str,
        offset: int,
    ) -> None:
        self.tag_type = tag_type
        self.data = data
        self.offset = offset

        # ROOT = -1
        # LITERAL = 0
        # SECTION = 2
        # INVERTED_SECTION = 3
        # PARTIAL = 5
        # VARIABLE = 6
        # VARIABLE_RAW = 7

        if tag_type in (
            TagType.ROOT,
            TagType.SECTION,
            TagType.INVERTED_SECTION,
        ):
            self.children = []
        else:
            self.children = None

    def recursive_display(self) -> str:
        res_str = self.__repr__() + "\n"

        if self.children is not None:
            for child in self.children:
                res_str += "    " + child.recursive_display() + "\n"

        return res_str

    def add_child(self, node: MustacheTreeNode) -> None:
        if self.children is None:
            raise NodeHasNoChildren(
                f"Mustache tree node of type {self.tag_type} has no children."
            )

        self.children.append(node)

    def __repr__(self) -> str:
        if self.data:
            return f"<{self.__class__.__name__}: {self.tag_type}, {self.data!r}>"
        return f"<{self.__class__.__name__}: {self.tag_type}>"


class MustacheRenderer:
    mustache_tree: MustacheTreeNode
    partials_dict: t.Dict[str, MustacheTreeNode]

    def __init__(
        self,
        mustache_tree: MustacheTreeNode,
        partials_dict: t.Optional[t.Dict[str, MustacheTreeNode]] = None,
    ) -> None:
        assert mustache_tree.tag_type is TagType.ROOT
        self.mustache_tree = mustache_tree

        if partials_dict is not None:
            for partial_tree in partials_dict.values():
                assert partial_tree.tag_type is TagType.ROOT

            self.partials_dict = partials_dict
        else:
            self.partials_dict = {}

    def render(
        self,
        data: ContextObjT,
        stringify: t.Callable[[t.Any], str] = str,
        html_escape_fn: t.Callable[[str], str] = html_escape,
    ) -> str:
        res_list = []
        starting_context = ContextNode(data)
        last_was_newline = True  # Track if we're at the start of a line

        assert self.mustache_tree.children is not None

        # Never need to read the root because it has no data
        work_deque: t.Deque[t.Tuple[MustacheTreeNode, ContextNode, int]] = deque(
            (node, starting_context, self.mustache_tree.offset)
            for node in self.mustache_tree.children
        )
        while work_deque:
            curr_node, curr_context, curr_offset = work_deque.popleft()
            if curr_node.tag_type is TagType.LITERAL:
                res_list.append(curr_node.data)
                last_was_newline = curr_node.data.endswith("\n")

                # Add offset for partials after newline, but only if there's
                # more content coming at the same offset level
                if last_was_newline and curr_offset > 0:
                    # Check if the next node also has the same offset
                    if work_deque and work_deque[0][2] == curr_offset:
                        res_list.append(curr_offset * " ")

            elif (
                curr_node.tag_type is TagType.VARIABLE
                or curr_node.tag_type is TagType.VARIABLE_RAW
            ):
                variable_content = curr_context.get(curr_node.data)
                if variable_content is not None:
                    str_content = stringify(variable_content)
                    # Skip ahead if we get the empty string
                    if not str_content:
                        continue
                    if curr_node.tag_type is TagType.VARIABLE:
                        str_content = html_escape_fn(str_content)

                    res_list.append(str_content)
            elif curr_node.tag_type is TagType.SECTION:
                new_context_stacks = curr_context.open_section(curr_node.data)

                assert curr_node.children is not None

                for new_context_stack in reversed(new_context_stacks):
                    for child_node in reversed(curr_node.children):
                        # No need to make a copy of the context per-child, it's immutable
                        work_deque.appendleft((child_node, new_context_stack, 0))

            elif curr_node.tag_type is TagType.INVERTED_SECTION:
                # No need to add to the context stack, inverted sections
                # by definition aren't in the namespace and can't add anything.
                lookup_data = curr_context.get(curr_node.data)

                assert curr_node.children is not None

                if not bool(lookup_data):
                    for child_node in reversed(curr_node.children):
                        work_deque.appendleft((child_node, curr_context, 0))

            elif curr_node.tag_type is TagType.PARTIAL:
                partial_tree = self.partials_dict.get(curr_node.data)

                if partial_tree is None:
                    continue

                assert partial_tree.children is not None

                # For standalone partials, add indentation at the beginning
                # Only add if we're at the start of a line (last output was newline)
                if curr_node.offset > 0 and last_was_newline:
                    res_list.append(curr_node.offset * " ")
                    last_was_newline = False

                # Propagate the combined offset through the partial content
                for child_node in reversed(partial_tree.children):
                    work_deque.appendleft(
                        (child_node, curr_context, curr_offset + curr_node.offset)
                    )

        return "".join(res_list)

    @classmethod
    def from_template(
        cls: t.Type[te.Self],
        template_str: str,
        partials: t.Optional[t.Dict[str, str]] = None,
    ) -> te.Self:
        partials_tree_dict = None

        if partials is not None:
            partials_tree_dict = {
                key: create_mustache_tree(partial_data)
                for key, partial_data in partials.items()
            }

        template_tree = create_mustache_tree(template_str)

        return cls(template_tree, partials_tree_dict)


def handle_final_line_clear(
    token_list: t.List, target_tokens: t.Tuple[TokenType, ...]
) -> None:
    if len(token_list) >= 2 and token_list[-1][0] in target_tokens:
        prev_type, prev_data, _ = token_list[-2]

        # Prev token is a whitespace literal we can possibly delete
        if (
            prev_type is TokenType.LITERAL
            and prev_data.isspace()
            and not prev_data.endswith("\n")
        ):
            # Delete if the previous token is a literal newline (if it exists)
            if len(token_list) == 2:
                token_list.pop(-2)
                return

            skip_prev_type, skip_prev_data, _ = token_list[-3]

            if skip_prev_type is TokenType.LITERAL and skip_prev_data.endswith("\n"):
                token_list.pop(-2)


def process_raw_token_list(
    raw_token_list: t.List[TokenTuple],
) -> t.List[TokenTuple]:
    indices_to_delete: t.Set[int] = set()
    res_token_list: t.List[TokenTuple] = []
    for i, token in enumerate(raw_token_list):
        token_type, token_data, token_offset = token

        curr_token_can_skip = (
            token_type is TokenType.LITERAL
            and token_data.isspace()
            and token_data.endswith("\n")
        )

        prev_token_can_skip = (
            len(res_token_list) >= 1 and res_token_list[-1][0] in _STANDALONE_TOKENS
        )

        remove_double_prev = False
        double_prev_can_skip = False

        # If the current token is a whitespace literal going onto the next line, and
        # the previous token is a token that should be on a standalone line.
        if curr_token_can_skip and prev_token_can_skip:
            if len(res_token_list) == 1:
                double_prev_can_skip = True
            # If the spaces behind the tag are a whitespace-only literal that
            # doesn't start a new line, get rid of it
            elif len(res_token_list) >= 2:
                double_prev_type, double_prev_data, _ = res_token_list[-2]

                if double_prev_type is TokenType.LITERAL:
                    double_prev_is_space = double_prev_data.isspace()
                    double_prev_ends_newline = double_prev_data.endswith("\n")
                    
                    if len(res_token_list) == 2:
                        remove_double_prev = (
                            double_prev_is_space and not double_prev_ends_newline
                        )

                        double_prev_can_skip = (
                            double_prev_is_space or double_prev_ends_newline
                        )
                    else:
                        triple_prev_type, triple_prev_data, _ = res_token_list[-3]
                        triple_prev_ends_newline = triple_prev_data.endswith("\n")
                        
                        remove_double_prev = (
                            double_prev_is_space
                            and not double_prev_ends_newline
                            and triple_prev_type is TokenType.LITERAL
                            and triple_prev_ends_newline
                        )

                        double_prev_can_skip = double_prev_ends_newline or (
                            double_prev_is_space
                            and triple_prev_type is TokenType.LITERAL
                            and triple_prev_ends_newline
                        )

            else:
                double_prev_can_skip = True

        # If we skip inserting the current token, try popping the one two tokens
        # ago if needed
        if double_prev_can_skip and prev_token_can_skip and curr_token_can_skip:
            indices_to_delete.add(i)
            if remove_double_prev:
                indices_to_delete.add(i - 2)

        res_token_list.append(token)

    handle_final_line_clear(res_token_list, _STANDALONE_TOKENS)
    # Don't require a trailing newline to remove leading whitespace.

    res_token_list = [
        elem for i, elem in enumerate(res_token_list) if i not in indices_to_delete
    ]

    return res_token_list


def create_mustache_tree(thing: str) -> MustacheTreeNode:
    root = MustacheTreeNode(TagType.ROOT, "", 0)
    work_stack: t.Deque[MustacheTreeNode] = deque([root])
    raw_token_list = mustache_tokenizer(thing)
    token_list = process_raw_token_list(raw_token_list)
    for token_type, token_data, token_offset in token_list:
        # token_data = token_data.decode("utf-8")
        if token_type is TokenType.LITERAL:
            literal_node = MustacheTreeNode(TagType.LITERAL, token_data, token_offset)
            work_stack[-1].add_child(literal_node)

        elif token_type in [TokenType.SECTION, TokenType.INVERTED_SECTION]:
            tag_type = (
                TagType.SECTION
                if token_type is TokenType.SECTION
                else TagType.INVERTED_SECTION
            )
            section_node = MustacheTreeNode(tag_type, token_data, token_offset)
            # Add section to list of children
            work_stack[-1].add_child(section_node)

            # Add section to work stack and descend in on the next iteration.
            work_stack.append(section_node)

        elif token_type is TokenType.END_SECTION:
            if work_stack[-1].data != token_data:
                raise StrayClosingTagError(f'Opening tag for "{token_data}" not found.')

            # Close the current section by popping off the end of the work stack.
            work_stack.pop()

        elif token_type in [TokenType.VARIABLE, TokenType.RAW_VARIABLE]:
            tag_type = (
                TagType.VARIABLE
                if token_type is TokenType.VARIABLE
                else TagType.VARIABLE_RAW
            )
            variable_node = MustacheTreeNode(tag_type, token_data, token_offset)
            # Add section to list of children

            work_stack[-1].add_child(variable_node)
        elif token_type is TokenType.COMMENT:
            pass
        elif token_type is TokenType.DELIMITER:
            # Delimiters don't add nodes to the tree, they're handled during tokenization
            pass
        elif token_type is TokenType.PARTIAL:
            partial_node = MustacheTreeNode(TagType.PARTIAL, token_data, token_offset)
            work_stack[-1].add_child(partial_node)
        else:
            raise MystaceError

    if work_stack[-1].tag_type is not TagType.ROOT:
        raise MissingClosingTagError(f"Missing closing tag for {work_stack[-1].data}")

    return root


def render_from_template(
    template: str,
    data: ContextObjT = None,
    partials: t.Optional[t.Dict[str, str]] = None,
    stringify: t.Callable[[t.Any], str] = str,
    html_escape_fn: t.Callable[[str], str] = html_escape,
) -> str:
    return MustacheRenderer.from_template(template, partials).render(
        data, stringify, html_escape_fn
    )
