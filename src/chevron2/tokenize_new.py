import typing as t
from enum import Enum

from . import exceptions as ex


class TokenType(Enum):
    COMMENT = 0
    RAW_VARIABLE = 1
    SECTION = 2
    INVERTED_SECTION = 3
    END_SECTION = 4
    DELIMITER = 5
    PARTIAL = 6
    VARIABLE = 8
    LITERAL = 9

    # TODO get rid of this funciton. I think this was only needed
    # if these were getting inserted into a heap, but they are not now.
    def __lt__(self, other: t.Any) -> bool:
        """
        From: https://stackoverflow.com/a/39269589
        """
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


class TokenTuple(t.NamedTuple):
    type: TokenType
    data: str
    offset: int  # used by partials to compute indentation.


def mustache_tokenizer(
    text: str,
    tags: t.Tuple[str, str] = (R"{{", R"}}"),
) -> t.List[TokenTuple]:
    # Different tokenizers to deal with the stupid delimiter swaps
    # text = text.encode()
    res_list = []
    start_tag, end_tag = tags
    end_literal = "}" + end_tag
    end_switch = "=" + end_tag
    cursor_loc = 0
    newline_offset = 0
    seen_tag_in_current_line = False

    while cursor_loc < len(text):
        next_tag_loc = text.find(start_tag, cursor_loc)
        # print(cursor_loc, next_tag_loc, next_newline_loc)
        # If we're at the tag location, yield it
        if cursor_loc == next_tag_loc:
            end_tag_to_search = "}}"

            tag_type_loc = cursor_loc + len(start_tag)
            offset = 1
            # print(len(start_tag))
            # print(str(text_bytes)[tag_type_loc], text_bytes[tag_type_loc], ord(b"#"))
            # '!': 'comment',
            # '#': 'section',
            # '^': 'inverted section',
            # '/': 'end',
            # '>': 'partial',
            # '=': 'set delimiter?',
            # '{': 'no escape?',
            # '&': 'no escape'
            # TODO do we want to render the empty string key for the
            # open brackets? We can probably revert to normal chevron
            # behavior in this case instead oft supporting this case.
            if tag_type_loc >= len(text):
                # TODO give a better error message.
                raise ex.Chevron2Error("Tag not closed.")
            elif text[tag_type_loc] == "!":
                new_token_type = TokenType.COMMENT
            elif text[tag_type_loc] == "#":
                new_token_type = TokenType.SECTION
            elif text[tag_type_loc] == "^":
                new_token_type = TokenType.INVERTED_SECTION
            elif text[tag_type_loc] == "/":
                new_token_type = TokenType.END_SECTION
            elif text[tag_type_loc] == ">":
                new_token_type = TokenType.PARTIAL
            elif text[tag_type_loc] == "=":
                # TODO the delimiter one needs more checks
                new_token_type = TokenType.DELIMITER
                end_tag_to_search = end_switch
            elif text[tag_type_loc] in ("{", "&"):
                # TODO maybe need to strip the inner thing more?
                new_token_type = TokenType.RAW_VARIABLE
                if text[tag_type_loc] == "{":
                    end_tag_to_search = end_literal
            else:
                # Just a variable
                new_token_type = TokenType.VARIABLE
                offset = 0

            end_loc = text.find(end_tag_to_search, cursor_loc)

            if end_loc == -1:
                raise ex.Chevron2Error("Tag not closed.")

            # This handles the "inline indentation" case, where a partial
            # doesn't get indented if it is not the first tag on a line
            if seen_tag_in_current_line:
                effective_newline_offset = 0
            else:
                effective_newline_offset = newline_offset

            # yield
            res_list.append(
                TokenTuple(
                    new_token_type,
                    text[cursor_loc + len(start_tag) + offset : end_loc].strip(),
                    effective_newline_offset,
                )
            )
            cursor_loc = len(end_tag_to_search) + end_loc
            seen_tag_in_current_line = True
            # print(cursor_loc)

        # Otherwise, yield the next literal, ending at newlines as-necessary
        else:
            next_literal_end = len(text)
            next_newline_loc = text.find("\n", cursor_loc)

            if next_newline_loc != -1:
                next_literal_end = min(next_literal_end, next_newline_loc + 1)

            if next_tag_loc != -1:
                next_literal_end = min(next_literal_end, next_tag_loc)

            literal_text = text[cursor_loc:next_literal_end]

            res_list.append(TokenTuple(TokenType.LITERAL, literal_text, newline_offset))

            if literal_text.endswith("\n"):
                newline_offset = 0
                seen_tag_in_current_line = False
            else:
                newline_offset += len(literal_text)

            cursor_loc = next_literal_end
    # print(res_list)
    return res_list
