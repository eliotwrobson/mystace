import enum
import html
import re
import typing as t

from .util import html_escape


class TagType(enum.Enum):
    VARIABLE = 0
    VARIABLE_RAW = 1
    RAW = 2
    SECTION = 3
    INVERTED_SECTION = 4
    PARTIAL = 5
    COMMENT = 6
    CLOSE = 7
    # Useful in to represent non-tags
    NONE = 8


class TokenType(t.NamedTuple):
    tag_key: str
    tag_type: TagType


def get_delimiter_dict() -> t.Dict[str, t.Tuple[str, TagType]]:
    # TODO add support for delimiter changes
    delimiter_dict = {
        r"{{": (r"}}", TagType.VARIABLE),
        r"{{{": (r"}}}", TagType.VARIABLE_RAW),
        r"{{&": (r"}}", TagType.RAW),
        r"{{#": (r"}}", TagType.SECTION),
        r"{{^": (r"}}", TagType.INVERTED_SECTION),
        r"{{>": (r"}}", TagType.PARTIAL),
        r"{{!": (r"}}", TagType.COMMENT),
        r"{{/": (r"}}", TagType.CLOSE),
    }

    return delimiter_dict


def generate_regex_from_literals() -> str:
    # TODO get away from hardcoding this
    literals = [
        r"{{!",
        r"{{#",
        r"{{^",
        r"{{/",
        r"{{>",
        r"{{{",
        r"{{&",
        r"}}}",
        # Had to put these last two last to give them last precedence
        r"{{",
        r"}}",
    ]
    # Escape special characters in literals and
    # join literals into a single pattern separated by '|'
    return "(" + "|".join(re.escape(literal) for literal in literals) + ")"


def generate_tokens_from_template(template: str) -> t.Generator[TokenType, None, None]:
    delimiter_dict = get_delimiter_dict()
    del_regex_pattern = generate_regex_from_literals()
    print(del_regex_pattern)

    token_iter = iter(re.split(del_regex_pattern, template))
    curr_sub_token = next(token_iter, None)
    while curr_sub_token is not None:
        if curr_sub_token in delimiter_dict:
            end_token, tag_type = delimiter_dict[curr_sub_token]
            tag_key = next(token_iter)
            expected_end_token = next(token_iter)

            assert expected_end_token == end_token

            yield TokenType(tag_key, tag_type)
        else:
            yield TokenType(curr_sub_token, TagType.NONE)

        curr_sub_token = next(token_iter, None)


class Context:
    __slots__ = ("stack",)

    stack: t.List[t.Tuple[t.Optional[str], t.Any]]

    # TODO come up with a data type to represent the initial data
    def __init__(self, initial_data) -> None:
        self.stack = [(None, initial_data)]

    # TODO this probably requires more key checking to actually work correctly
    @staticmethod
    def check_context_for_key(context, key_tuple: t.Tuple[str, ...]):
        # Lookup stops if we hit a dot
        if not key_tuple:
            return context

        for key_item in key_tuple:
            if key_item not in context:
                return None

            # TODO need to correctly distinguish the case where the
            # value could be None
            context = context[key_item]

        return context

    def get_from_context(self, key: str):
        if key == ".":
            return self.stack[-1][1]

        key_tuple = key.split(".")
        # Search for possible contexts starting from the top
        for _, context in reversed(self.stack):
            key_value = self.check_context_for_key(context, key_tuple)
            if key_value is not None:
                return key_value
        return None

    def open_section(self, key: str) -> bool:
        new_context = self.get_from_context(key)
        print(key, new_context, self.stack)
        if new_context:
            self.stack.append((key, new_context))
            return True

        return False

    def close_section(self, key: str) -> None:
        print(self.stack)
        if self.stack[-1][0] != key:
            raise Exception
        self.stack.pop()


def tokenize(template: str, data: t.Any) -> str:
    render_context = Context(data)
    res_list = []

    for token in generate_tokens_from_template(template):
        print(token, res_list)
        if token.tag_type == TagType.NONE:
            res_list.append(token.tag_key)
        elif token.tag_type == TagType.COMMENT:
            continue
        elif token.tag_type == TagType.VARIABLE:
            content = render_context.get_from_context(token.tag_key)
            if content:
                res_list.append(html_escape(str(content)))
        elif token.tag_type == TagType.VARIABLE_RAW:
            content = render_context.get_from_context(token.tag_key)
            if content:
                res_list.append(str(content))
        elif token.tag_type == TagType.SECTION:
            # This is the context that will be used in the next section
            render_context.open_section(token.tag_key)
        elif token.tag_type == TagType.CLOSE:
            # Closing the current context. Checks that the key matches.
            render_context.close_section(token.tag_key)

    return "".join(res_list)
