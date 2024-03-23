#!/usr/bin/env python
# -*- coding: utf-8 -*-

import heapq
import re
import typing as t
from enum import Enum

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


class TokenTuple(t.NamedTuple):
    # TODO add "offset" as an attribute to this tuple, will be used
    # by partials to compute indentation.
    type: TokenType
    data: str


class HeapToken(t.NamedTuple):
    loc: int
    type: TokenType
    next_match: re.Match
    pattern: re.Pattern


class TokenCursor:
    """
    A token cursor, yielding tokens with a given delimiter.
    """

    token_heap: t.List[HeapToken]
    cursor_loc: int
    text: str
    _remainder: t.Optional[TokenTuple]

    def __init__(self, text: str, left_delim: str, right_delim: str) -> None:
        left_delim = re.escape(left_delim)
        right_delim = re.escape(right_delim)

        comment_pattern = r"(?s)" + left_delim + r"\!(.*?)" + right_delim
        token_pattern = left_delim + r"(.*?)" + right_delim
        raw_token_pattern = left_delim + r"\{(.*?)\}" + right_delim

        # Using inline flags for more control over behavior, see
        # https://docs.python.org/3/library/re.html#re.DOTALL
        # patterns = [
        #     (TokenType.COMMENT, r"(?s)" + left_delim + r"\!(.*?)" + right_delim),
        #     (TokenType.RAW_VARIABLE, left_delim + r"\{(.*?)\}" + right_delim),
        #     (TokenType.RAW_VARIABLE, left_delim + r"\&(.*?)" + right_delim),
        #     (TokenType.SECTION, left_delim + r"\#(.*?)" + right_delim),
        #     (TokenType.INVERTED_SECTION, left_delim + r"\^(.*?)" + right_delim),
        #     (TokenType.END_SECTION, left_delim + r"/(.*?)" + right_delim),
        #     (TokenType.DELIMITER, left_delim + r"=(.*?)=" + right_delim),
        #     (TokenType.PARTIAL, left_delim + r">(.*?)" + right_delim),
        #     (TokenType.VARIABLE, left_delim + r"(.*?)" + right_delim),
        # ]

        # token_heap = []

        # for token_type, pattern_str in patterns:
        #     pattern = re.compile(pattern_str)
        #     match = pattern.search(text)

        #     if match is None:
        #         continue

        #     token_heap.append(HeapToken(match.start(), token_type, match, pattern))

        # heapq.heapify(token_heap)

        # self.token_heap = token_heap
        self.cursor_loc = 0
        self.text = text
        self._remainder = None

    def get_next_token(self) -> t.Optional[TokenTuple]:
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

            if newline_loc == -1 or newline_loc == len(self.text) - 1:
                res_string = self.text[self.cursor_loc : len(self.text)]
                self.cursor_loc = len(self.text)
                return TokenTuple(TokenType.LITERAL, res_string)

            first_res_string = self.text[self.cursor_loc : newline_loc + 1]
            second_res_string = self.text[newline_loc + 1 : len(self.text)]
            self._remainder = TokenTuple(TokenType.LITERAL, second_res_string)

            return TokenTuple(TokenType.LITERAL, first_res_string)

        elif self.token_heap[0].loc > self.cursor_loc:
            next_event_loc = self.token_heap[0].loc

            # TODO to speed this up, use rfind to get the last location before
            # the next tag event.
            # NOTE I think the edge case here is if the newline is
            # at the location of the current cursor.
            # TODO use a method call to do this and cache the location based on the cursor,
            # or just read all newline locations from the beginning. I'm pretty sure this is
            # what's causing the slowdown in some test cases.
            newline_idx = self.text.find("\n", self.cursor_loc)
            # newline_idx = self.text.rfind("\n", self.cursor_loc, next_event_loc - 1)

            # assert newline_idx == self.text.rfind("\n", self.cursor_loc, next_event_loc)
            if newline_idx >= 0:
                next_event_loc = min(newline_idx + 1, next_event_loc)

            literal_string = self.text[self.cursor_loc : next_event_loc]

            self.cursor_loc = next_event_loc
            return TokenTuple(TokenType.LITERAL, literal_string)

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
                    HeapToken(next_match.start(), token_type, next_match, pattern),
                )

        self.cursor_loc = next_event_loc
        return TokenTuple(new_token_type, new_token_data)


def mustache_tokenizer(text: str) -> t.List[TokenTuple]:
    # Different tokenizers to deal with the stupid delimiter swaps
    first_cursor = TokenCursor(text, R"{{", R"}}")
    res_token_list = []
    tokenizer_stack = [first_cursor]

    while tokenizer_stack:
        curr_tokenizer = tokenizer_stack.pop()

        curr_token = curr_tokenizer.get_next_token()

        while curr_token is not None:
            # token_type, data = curr_token

            if curr_token.type is TokenType.DELIMITER:
                raise Exception("Need to implement this case.")

            res_token_list.append(curr_token)

            curr_token = curr_tokenizer.get_next_token()

    # Ensures tokenization worked as expected
    # NOTE must change match group data to get this to pass
    # assert text == "".join(test_thing)
    return res_token_list
