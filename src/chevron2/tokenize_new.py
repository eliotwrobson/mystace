import heapq
import re
import typing as t
from enum import Enum

from icecream import ic

# '!': 'comment',
# '#': 'section',
# '^': 'inverted section',
# '/': 'end',
# '>': 'partial',
# '=': 'set delimiter?',
# '{': 'no escape?',
# '&': 'no escape'


# Numerical values here will be used to break ties in the heap


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


class Token(t.NamedTuple):
    loc: int
    type: TokenType
    next_match: re.Match[str]
    pattern: re.Pattern


class TokenCursor:
    """
    A token cursor, yielding tokens with a given delimiter.
    """

    token_heap: t.List[Token]
    cursor_loc: int
    text: str
    _remainder: t.Optional[t.Tuple[TokenType, str]]

    def __init__(self, text: str, right_delim: str, left_delim: str) -> None:
        # Using inline flags for more control over behavior, see
        # https://docs.python.org/3/library/re.html#re.DOTALL
        patterns = [
            (TokenType.COMMENT, r"(?s)\{\{!(.*?)\}\}"),
            (TokenType.RAW_VARIABLE, r"\{\{\{(.*?)\}\}\}"),
            (TokenType.RAW_VARIABLE, r"\{\{&(.*?)\}\}"),
            (TokenType.SECTION, r"\{\{#(.*?)\}\}"),
            (TokenType.INVERTED_SECTION, r"\{\{\^(.*?)\}\}"),
            (TokenType.END_SECTION, r"\{\{/(.*?)\}\}"),
            (TokenType.DELIMITER, r"\{\{=(.*?)=\}\}"),
            (TokenType.PARTIAL, r"\{\{>(.*?)\}\}"),
            (TokenType.VARIABLE, r"\{\{(.*?)\}\}"),
        ]

        token_heap = []

        for token_type, pattern_str in patterns:
            pattern = re.compile(pattern_str)
            match = pattern.search(text)

            if match is None:
                continue

            # print(pattern, match.start())
            token_heap.append(Token(match.start(), token_type, match, pattern))

        heapq.heapify(token_heap)

        self.token_heap = token_heap
        self.cursor_loc = 0
        self.text = text
        self._remainder = None

    def get_next_token(self) -> t.Optional[t.Tuple[TokenType, str]]:
        if self._remainder is not None:
            res = self._remainder
            self._remainder = None
            self.cursor_loc = len(self.text)

            return res

        # If at the end, no more tokens, so just return None
        elif self.cursor_loc == len(self.text):
            return None

        # If no more tokens, return the final literal
        elif not self.token_heap:
            newline_loc = self.text.find("\n", self.cursor_loc)
            # print("HERE")
            # print(
            #     repr(self.text[self.cursor_loc : len(self.text)]),
            #     newline_loc,
            #     self.cursor_loc,
            #     len(self.text),
            # )
            if (
                newline_loc == -1
                or newline_loc == self.cursor_loc == len(self.text) - 1
            ):
                print("repr: ", repr(self.text[self.cursor_loc : len(self.text)]))
                res_string = self.text[self.cursor_loc : len(self.text)]
                self.cursor_loc = len(self.text)
                return TokenType.LITERAL, res_string

            first_res_string = self.text[self.cursor_loc : newline_loc + 1]
            second_res_string = self.text[newline_loc + 1 : len(self.text)]
            # print("first: ", repr(first_res_string))
            # print("second: ", repr(second_res_string))
            self._remainder = (TokenType.LITERAL, second_res_string)

            return TokenType.LITERAL, first_res_string

        elif self.token_heap[0].loc > self.cursor_loc:
            next_event_loc = self.token_heap[0].loc

            # TODO to speed this up, use rfind to get the last location before
            # the next tag event.
            newline_idx = self.text.find("\n", self.cursor_loc)
            # ic(self.text[self.cursor_loc : self.cursor_loc + 5])
            # ic(newline_idx)
            if newline_idx >= 0:
                next_event_loc = min(newline_idx + 1, next_event_loc)

            literal_string = self.text[self.cursor_loc : next_event_loc]
            # ic(literal_string)
            self.cursor_loc = next_event_loc
            return TokenType.LITERAL, literal_string

        new_token_type = self.token_heap[0].type
        # NOTE This uses the fact that each match group has a single unknown.
        new_token_data = self.token_heap[0].next_match.group(1).strip()

        next_event_loc = self.token_heap[0].next_match.end()
        # Remove all stale tokens, update them by searching ahead of the location of the current cursor
        while self.token_heap and self.token_heap[0].loc < next_event_loc:
            start_loc, token_type, match_obj, pattern = heapq.heappop(self.token_heap)
            next_match = pattern.search(self.text, next_event_loc)

            # If match is none, this pattern doesn't appear in the text anymore, so we
            # can just throw away.
            if next_match is not None:
                heapq.heappush(
                    self.token_heap,
                    Token(next_match.start(), token_type, next_match, pattern),
                )

        self.cursor_loc = next_event_loc
        return new_token_type, new_token_data


def mustache_tokenizer(text: str) -> t.List[t.Tuple[TokenType, str]]:
    # Different tokenizers to deal with the stupid delimiter swaps
    first_cursor = TokenCursor(text, r"\{\{", r"\}\}")
    res_token_list = []
    tokenizer_stack = [first_cursor]
    # test_thing = []

    while tokenizer_stack:
        curr_tokenizer = tokenizer_stack.pop()

        curr_token = curr_tokenizer.get_next_token()

        while curr_token is not None:
            token_type, data = curr_token
            # test_thing.append(data)
            if token_type is TokenType.DELIMITER:
                raise Exception("Need to implement this case.")
            # Need to add comments to the list of tokens because of whitespace issues.

            # ic(curr_token)

            res_token_list.append(curr_token)

            # clear_whitespace_surrounding_tag(res_token_list)

            curr_token = curr_tokenizer.get_next_token()

    # Ensures tokenization worked as expected
    # NOTE must change match group data to get this to pass
    # assert text == "".join(test_thing)
    # ic(res_token_list)
    # print(res_token_list)
    return res_token_list


ic("hey")


def clear_whitespace_surrounding_tag(
    token_list: t.List[t.Tuple[TokenType, str]],
) -> None:
    """
    Check the last three indices to see if we need to clear the whitespace around a
    tag.
    """

    TARGET_TOKENS = (
        TokenType.COMMENT,
        TokenType.END_SECTION,
        TokenType.INVERTED_SECTION,
    )

    if len(token_list) < 2:
        return

    prev_type, prev_data = token_list[-2]
    curr_type, curr_data = token_list[-1]
    print("about to remove: ", token_list)
    # TODO the removal here is causing a bug with the
    if curr_type in TARGET_TOKENS:
        if (
            prev_type is TokenType.LITERAL
            and (prev_data.isspace() and prev_data != "\n")
            and (len(token_list) < 3 or token_list[-3][0] is TokenType.LITERAL)
        ):
            token_list.pop(-2)
            return
    elif curr_type is TokenType.LITERAL and curr_data.isspace():
        if prev_type in TARGET_TOKENS:
            if (
                len(token_list) < 3
                or token_list[-3][0] is not TokenType.LITERAL
                or token_list[-3][1].endswith("\n")
            ):
                token_list[-1] = (TokenType.LITERAL, "")
                return
