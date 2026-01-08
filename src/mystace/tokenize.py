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
    res_list = []
    res_list_append = res_list.append  # Cache method lookup
    start_tag, end_tag = tags
    start_tag_len = len(start_tag)  # Cache length
    end_literal = "}" + end_tag
    end_switch = "=" + end_tag
    text_len = len(text)  # Cache length
    cursor_loc = 0
    newline_offset = 0
    seen_tag_in_current_line = False
    
    # Pre-compute TokenTypes to avoid enum lookups
    TOKEN_COMMENT = TokenType.COMMENT
    TOKEN_SECTION = TokenType.SECTION
    TOKEN_INVERTED_SECTION = TokenType.INVERTED_SECTION
    TOKEN_END_SECTION = TokenType.END_SECTION
    TOKEN_PARTIAL = TokenType.PARTIAL
    TOKEN_DELIMITER = TokenType.DELIMITER
    TOKEN_RAW_VARIABLE = TokenType.RAW_VARIABLE
    TOKEN_VARIABLE = TokenType.VARIABLE
    TOKEN_LITERAL = TokenType.LITERAL

    while cursor_loc < text_len:
        next_tag_loc = text.find(start_tag, cursor_loc)
        # If we're at the tag location, yield it
        if cursor_loc == next_tag_loc:
            end_tag_to_search = end_tag

            tag_type_loc = cursor_loc + start_tag_len
            offset = 1
            # '!': 'comment',
            # '#': 'section',
            # '^': 'inverted section',
            # '/': 'end',
            # '>': 'partial',
            # '=': 'set delimiter?',
            # '{': 'no escape?',
            # '&': 'no escape'
            if tag_type_loc >= text_len:
                raise ex.MystaceError("Tag not closed.")
            
            char = text[tag_type_loc]
            if char == "!":
                new_token_type = TOKEN_COMMENT
            elif char == "#":
                new_token_type = TOKEN_SECTION
            elif char == "^":
                new_token_type = TOKEN_INVERTED_SECTION
            elif char == "/":
                new_token_type = TOKEN_END_SECTION
            elif char == ">":
                new_token_type = TOKEN_PARTIAL
            elif char == "=":
                new_token_type = TOKEN_DELIMITER
                end_tag_to_search = end_switch
                offset = 1
            elif char == "{" or char == "&":
                new_token_type = TOKEN_RAW_VARIABLE
                if char == "{":
                    end_tag_to_search = end_literal
            else:
                # Just a variable
                new_token_type = TOKEN_VARIABLE
                offset = 0

            # Search for end tag starting after the start tag and any offset
            search_start = cursor_loc + start_tag_len + offset
            end_loc = text.find(end_tag_to_search, search_start)

            if end_loc == -1:
                raise ex.MystaceError("Tag not closed.")

            # This handles the "inline indentation" case, where a partial
            # doesn't get indented if it is not the first tag on a line
            effective_newline_offset = 0 if seen_tag_in_current_line else newline_offset

            # yield
            token_content = text[cursor_loc + start_tag_len + offset : end_loc].strip()
            res_list_append(
                TokenTuple(
                    new_token_type,
                    token_content,
                    effective_newline_offset,
                )
            )
            cursor_loc = len(end_tag_to_search) + end_loc
            seen_tag_in_current_line = True

            # Handle delimiter changes
            if new_token_type == TOKEN_DELIMITER:
                # Parse new delimiters from token content
                parts = token_content.split()
                if len(parts) != 2:
                    raise ex.DelimiterError(
                        f"Delimiter tag must contain exactly 2 delimiters, got {len(parts)}"
                    )
                start_tag, end_tag = parts
                start_tag_len = len(start_tag)  # Update cached length
                # Update all the computed end tags
                end_literal = "}" + end_tag
                end_switch = "=" + end_tag

        # Otherwise, yield the next literal, ending at newlines as-necessary
        else:
            next_literal_end = text_len
            next_newline_loc = text.find("\n", cursor_loc)

            if next_newline_loc != -1:
                next_literal_end = min(next_literal_end, next_newline_loc + 1)

            if next_tag_loc != -1:
                next_literal_end = min(next_literal_end, next_tag_loc)

            literal_text = text[cursor_loc:next_literal_end]

            res_list_append(TokenTuple(TOKEN_LITERAL, literal_text, newline_offset))

            if literal_text.endswith("\n"):
                newline_offset = 0
                seen_tag_in_current_line = False
            else:
                newline_offset += len(literal_text)

            cursor_loc = next_literal_end
    return res_list
