#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import typing as t
from enum import Enum

from more_itertools import peekable

TOKEN_TYPES = [(True, False, True, False)] * 0x100
TOKEN_TYPES[0x21] = False, False, False, True  # '!'
TOKEN_TYPES[0x23] = False, True, True, False  # '#'
TOKEN_TYPES[0x26] = True, True, True, True  # '&'
TOKEN_TYPES[0x2F] = False, True, False, False  # '/'
TOKEN_TYPES[0x3D] = False, False, False, False  # '='
TOKEN_TYPES[0x3E] = False, False, True, False  # '>'
TOKEN_TYPES[0x5E] = False, True, True, True  # '^'
TOKEN_TYPES[0x7B] = True, True, False, True  # '{'


def slicestrip(template: bytes, start: int, end: int) -> slice:
    """
    Strip slice from whitespace on bytes.

    :param template: bytes where whitespace should be stripped
    :param start: substring slice start
    :param end: substring slice end
    :returns: resulting stripped slice

    """
    c = template[start:end]
    return slice(end - len(c.lstrip()), start + len(c.rstrip()))


def tokenize(
    template: bytes,
    *,
    tags: t.Tuple[bytes, bytes] = (Rb"{{", Rb"}}"),
    comments: bool = False,
):
    """
    Generate token tuples from mustache template.

    This generator accepts sending back a token index, which will result on
    rewinding it back and repeat everything from there.

    :param template: template as utf-8 encoded bytes
    :param tags: mustache tag tuple (open, close)
    :param comments: whether yield comment tokens or not (ignore comments)
    :param cache: mutable mapping for compiled template cache
    :return: token tuple generator (type, name slice, content slice, option)

    :raises UnclosedTokenException: if token is left unclosed
    :raises ClosingTokenException: if block closing token does not match
    :raises DelimiterTokenException: if delimiter token syntax is invalid

    """
    EMPTY = slice(0)
    EVERYTHING = slice(None)

    template_find = template.find

    stack = []
    stack_append = stack.append
    stack_pop = stack.pop
    scope_label = EVERYTHING
    scope_head = 0
    scope_start = 0
    scope_index = 0

    empty = EMPTY
    start_tag, end_tag = tags
    end_literal = b"}" + end_tag
    end_switch = b"=" + end_tag
    start_len = len(start_tag)
    end_len = len(end_tag)

    # token: CompiledToken
    token_types = TOKEN_TYPES
    t = slice
    import functools

    s = functools.partial(slicestrip, template)

    text_start, text_end = 0, template_find(start_tag)
    while text_end != -1:
        if text_start < text_end:  # text
            token = False, True, False, empty, t(text_start, text_end), -1
            yield token

        tag_start = text_end + start_len
        try:
            print(template[tag_start])
            a, b, c, d = token_types[template[tag_start]]
        except IndexError:
            raise ValueError

        if a:  # variables
            tag_start += b

            if c:  # variable
                tag_end = template_find(end_tag, tag_start)
                text_start = tag_end + end_len

            else:  # triple-keyed variable
                tag_end = template_find(end_literal, tag_start)
                text_start = tag_end + end_len + 1

            token = False, True, True, s(tag_start, tag_end), empty, d

        elif b:  # block
            tag_start += 1
            tag_end = template_find(end_tag, tag_start)
            text_start = tag_end + end_len

            if c:  # open
                stack_append((scope_label, text_end, scope_start, scope_index))
                scope_label = s(tag_start, tag_end)
                scope_head = text_end
                scope_start = text_start
                scope_index = -1  # len(recording)
                token = True, True, False, scope_label, empty, d

            elif template[scope_label] != template[tag_start:tag_end].strip():
                raise ValueError

            else:  # close
                token = (
                    True,
                    True,
                    True,
                    scope_label,
                    s(scope_start, text_end),
                    scope_index,
                )
                scope_label, scope_head, scope_start, scope_index = stack_pop()

        elif c:  # partial
            tag_start += 1
            tag_end = template_find(end_tag, tag_start)
            text_start = tag_end + end_len
            token = True, False, True, s(tag_start, tag_end), empty, -1

        elif d:  # comment
            tag_start += 1
            tag_end = template_find(end_tag, tag_start)
            text_start = tag_end + end_len

            if not comments:
                text_end = template_find(start_tag, text_start)
                continue

            token = True, False, False, empty, s(tag_start, tag_end), -1

        else:  # tags
            tag_start += 1
            tag_end = template_find(end_switch, tag_start)
            text_start = tag_end + end_len + 1

            try:
                start_tag, end_tag = template[tag_start:tag_end].split(b" ")
                if not (start_tag and end_tag):
                    raise ValueError

            except ValueError:
                raise ValueError

            end_literal = b"}" + end_tag
            end_switch = b"=" + end_tag
            start_len = len(start_tag)
            end_len = len(end_tag)
            start_end = tag_start + start_len
            end_start = tag_end - end_len
            token = (
                False,
                False,
                True,
                s(tag_start, start_end),
                s(end_start, tag_end),
                -1,
            )

        if tag_end < 0:
            raise ValueError

        text_end = template_find(start_tag, text_start)

    if stack:
        raise ValueError

    # end
    token = False, False, False, empty, t(text_start, None), -1
    yield token


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


def mustache_tokenizer(
    text: str,
    tags: t.Tuple[bytes, bytes] = (Rb"{{", Rb"}}"),
) -> t.List[TokenTuple]:
    # Different tokenizers to deal with the stupid delimiter swaps
    text_bytes = text.encode()
    res_list = []
    start_tag, end_tag = tags
    end_literal = b"}" + end_tag
    end_switch = b"=" + end_tag
    cursor_loc = 0

    while cursor_loc < len(text_bytes):
        if len(res_list) > 100:
            print(res_list)
            exit()

        next_tag_loc = text_bytes.find(start_tag, cursor_loc)
        next_newline_loc = text_bytes.find(b"\n", cursor_loc)
        # print(cursor_loc, next_tag_loc, next_newline_loc)
        # If we're at the tag location, yield it
        if cursor_loc == next_tag_loc:
            end_tag_to_search = b"}}"

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
            if text_bytes[tag_type_loc] == ord(b"!"):
                new_token_type = TokenType.VARIABLE
            elif text_bytes[tag_type_loc] == ord(b"#"):
                new_token_type = TokenType.SECTION
            elif text_bytes[tag_type_loc] == ord(b"^"):
                new_token_type = TokenType.INVERTED_SECTION
            elif text_bytes[tag_type_loc] == ord(b"/"):
                new_token_type = TokenType.END_SECTION
            elif text_bytes[tag_type_loc] == ord(b">"):
                new_token_type = TokenType.PARTIAL
            elif text_bytes[tag_type_loc] == ord(b"="):
                # TODO the delimiter one needs more checks
                new_token_type = TokenType.DELIMITER
                end_tag_to_search = end_switch
            elif text_bytes[tag_type_loc] in (ord(b"{"), ord(b"&")):
                # TODO maybe need to strip the inner thing more?
                new_token_type = TokenType.RAW_VARIABLE
                if text_bytes[tag_type_loc] == ord(b"{"):
                    end_tag_to_search = end_literal
            else:
                # Just a variable
                new_token_type = TokenType.VARIABLE
                offset = 0

            end_loc = text_bytes.find(end_tag_to_search, cursor_loc)

            # yield
            res_list.append(
                TokenTuple(
                    new_token_type,
                    text_bytes[cursor_loc + len(start_tag) + offset : end_loc],
                )
            )
            cursor_loc = len(end_tag_to_search) + end_loc
            print(cursor_loc)

        # Otherwise, yield the next literal, ending at newlines as-necessary
        else:
            next_literal_end = len(text_bytes)

            if next_newline_loc != -1:
                next_literal_end = min(next_literal_end, next_newline_loc) + 1

            if next_tag_loc != -1:
                next_literal_end = min(next_literal_end, next_tag_loc)

            res_list.append(
                TokenTuple(TokenType.LITERAL, text_bytes[cursor_loc:next_literal_end])
            )

            cursor_loc = next_literal_end

    return res_list
