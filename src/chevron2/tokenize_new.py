#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import typing as t
from enum import Enum

from more_itertools import peekable

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

        # full_pattern = token_pattern + "|" + raw_token_pattern

        regex_pattern_comp = re.compile(token_pattern)
        comment_pattern_comp = re.compile(comment_pattern)
        raw_pattern_comp = re.compile(raw_token_pattern)

        self.match_iter = peekable(regex_pattern_comp.finditer(text))
        self.comment_iter = peekable(comment_pattern_comp.finditer(text))
        self.raw_iter = peekable(raw_pattern_comp.finditer(text))

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

        # TODO use a list for this.

        for iterator in (self.match_iter, self.comment_iter, self.raw_iter):
            # Advance iterators if cursor has moved.
            while iterator and iterator.peek().start() < self.cursor_loc:
                next(iterator)

        # NOTE we have to match comments first because the pattern overlaps
        # with the main one.
        next_comment = self.comment_iter.peek(None)

        # If we're at the current match
        if next_comment is not None and next_comment.start() == self.cursor_loc:
            # NOTE This uses the fact that each match group has a single unknown.
            # new_token_data = "".join(next_comment.group(1).split())

            # '!': 'comment'
            # Advance token iterator and cursor
            next(self.comment_iter)
            self.cursor_loc = next_comment.end()

            # No need to include contents of the comment,
            # just keep track of where it started and ended.
            return TokenTuple(TokenType.COMMENT, "")

        next_raw = self.raw_iter.peek(None)
        if next_raw is not None and next_raw.start() == self.cursor_loc:
            # NOTE This uses the fact that each match group has a single unknown.
            new_token_data = "".join(next_raw.group(1).split())

            next(self.raw_iter)
            self.cursor_loc = next_raw.end()

            # No need to include contents of the comment,
            # just keep track of where it started and ended.
            return TokenTuple(TokenType.RAW_VARIABLE, new_token_data)

        next_match = self.match_iter.peek(None)

        # If we're at the current match
        if next_match is not None and next_match.start() == self.cursor_loc:
            # NOTE This uses the fact that each match group has a single unknown.
            new_token_data = "".join(next_match.group(1).split())

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
            if not new_token_data:
                new_token_type = TokenType.VARIABLE
            elif new_token_data[0] == "#":
                new_token_type = TokenType.SECTION
                new_token_data = new_token_data[1:]
            elif new_token_data[0] == "^":
                new_token_type = TokenType.INVERTED_SECTION
                new_token_data = new_token_data[1:]
            elif new_token_data[0] == "/":
                new_token_type = TokenType.END_SECTION
                new_token_data = new_token_data[1:]
            elif new_token_data[0] == ">":
                new_token_type = TokenType.PARTIAL
                new_token_data = new_token_data[1:]
            elif new_token_data[0] == "=":
                # TODO the delimiter one needs more checks
                new_token_type = TokenType.DELIMITER
            elif new_token_data[0] in ("{", "&"):
                # TODO maybe need to strip the inner thing more?
                new_token_type = TokenType.RAW_VARIABLE
                if new_token_data[0] == "&":
                    new_token_data = new_token_data[1:]
            else:
                # Just a variable
                new_token_type = TokenType.VARIABLE

            # Advance token iterator and cursor
            next(self.match_iter)
            self.cursor_loc = next_match.end()

            return TokenTuple(new_token_type, new_token_data)

        # If neither match worked, then we have a literal.
        # If no more tokens, return the final literal
        if next_match is None and next_comment is None:
            newline_loc = self.text.find("\n", self.cursor_loc)

            if newline_loc == -1 or newline_loc == len(self.text) - 1:
                res_string = self.text[self.cursor_loc : len(self.text)]
                self.cursor_loc = len(self.text)
                return TokenTuple(TokenType.LITERAL, res_string)

            first_res_string = self.text[self.cursor_loc : newline_loc + 1]
            second_res_string = self.text[newline_loc + 1 : len(self.text)]
            self._remainder = TokenTuple(TokenType.LITERAL, second_res_string)

            return TokenTuple(TokenType.LITERAL, first_res_string)

        next_cursor_loc = len(self.text)

        for match_obj in (next_match, next_comment, next_raw):
            if match_obj is not None:
                next_cursor_loc = min(next_cursor_loc, match_obj.start())

        newline_idx = self.text.find("\n", self.cursor_loc)

        # TODO maybe can use rfind to put literals together more efficiently.
        # assert newline_idx == self.text.rfind("\n", self.cursor_loc, next_event_loc)
        if newline_idx >= 0:
            next_cursor_loc = min(newline_idx + 1, next_cursor_loc)

        literal_string = self.text[self.cursor_loc : next_cursor_loc]

        self.cursor_loc = next_cursor_loc
        return TokenTuple(TokenType.LITERAL, literal_string)


def mustache_tokenizer(text: str) -> t.List[TokenTuple]:
    # Different tokenizers to deal with the stupid delimiter swaps
    first_cursor = TokenCursor(text, R"{{", R"}}")
    res_token_list = []
    tokenizer_stack = [first_cursor]
    i = 0
    # print("text: ", text)
    while tokenizer_stack:
        curr_tokenizer = tokenizer_stack.pop()

        curr_token = curr_tokenizer.get_next_token()

        while curr_token is not None:
            # i += 1

            # if i > 100:
            #     print(res_token_list)
            #     assert False
            # token_type, data = curr_token

            if curr_token.type is TokenType.DELIMITER:
                raise Exception("Need to implement this case.")

            res_token_list.append(curr_token)

            curr_token = curr_tokenizer.get_next_token()

    # Ensures tokenization worked as expected
    # NOTE must change match group data to get this to pass
    # assert text == "".join(test_thing)
    # print(res_token_list)
    return res_token_list
