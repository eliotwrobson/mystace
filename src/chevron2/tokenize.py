import enum
import re
import typing as t


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


def generate_regex_from_literals(literals: t.Set[str]) -> str:
    # Escape special characters in literals and
    # join literals into a single pattern separated by '|'
    return "(" + "|".join(re.escape(literal) for literal in literals) + ")"


def generate_tokens_from_template(template: str) -> t.Generator[TokenType, None, None]:
    delimiter_dict = get_delimiter_dict()

    delimiters = set(delimiter_dict.keys())
    delimiters.update(end_del for end_del, _ in delimiter_dict.values())

    del_regex_pattern = generate_regex_from_literals(delimiters)

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


def tokenize(template: str):
    for token in generate_tokens_from_template(template):
        print(token)
