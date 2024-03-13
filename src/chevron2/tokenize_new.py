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
    VARIABLE = 2
    DELIMITER = 4
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

    def __init__(self, text: str, right_delim: str, left_delim: str) -> None:
        patterns = [
            (TokenType.RAW_VARIABLE, r"\{\{(.*?)\}\}"),
            (TokenType.DELIMITER, r"\{\{=(.*?)=\}\}"),
        ]

        token_heap = []

        for token_type, pattern_str in patterns:
            pattern = re.compile(pattern_str)
            match = pattern.search(text)

            if match is None:
                continue

            print(pattern, match.start())
            token_heap.append(Token(match.start(), token_type, match, pattern))

        heapq.heapify(token_heap)

        self.token_heap = token_heap
        self.cursor_loc = 0
        self.text = text

    def get_next_token(self) -> t.Optional[t.Tuple[TokenType, str]]:
        # If all searchers are ahead, return a literal
        if self.token_heap[0].loc > self.cursor_loc:
            literal_string = self.text[self.cursor_loc, self.token_heap[0].loc]
            self.cursor_loc = self.token_heap[0].loc
            return TokenType.LITERAL, literal_string

        start_loc, token_type, match_obj, pattern = heapq.heappop(self.token_heap)

        end_loc = match_obj.end()
        self.cursor_loc = max(end_loc, self.cursor_loc)
        next_match = pattern.search(self.text, end_loc)

        # If match is none, this pattern doesn't appear in the text anymore, so we
        # can just throw away.
        if next_match is not None:
            heapq.heappush(
                self.token_heap,
                Token(next_match.start(), token_type, next_match, pattern),
            )

        return token_type, match_obj


def mustache_tokenizer(text: str) -> t.List[t.Tuple[TokenType, str]]:
    # Different tokenizers to deal with the stupid delimiter swaps
    first_cursor = TokenCursor()
    res_token_list = []
    tokenizer_stack = [first_cursor]

    while tokenizer_stack:
        curr_tokenizer = tokenizer_stack.pop()

        curr_token = curr_tokenizer.get_next_token()

        while curr_token is not None:
            token_type, data = curr_token

            if token_type is TokenType.DELIMITER:
                raise Exception("Need to implement this case.")

            res_token_list.append(curr_token)

            curr_token = curr_tokenizer.get_next_token()

    return res_token_list


class MustacheTokenizer:
    """A class that yields ."""

    # __slots__: t.Tuple[str, ...] = ("_tokens",)

    token_heap: t.List[Token]
    text: str

    def __init__(self, text: str, patterns: t.List[t.Tuple[TokenType, str]]) -> None:
        self.text = text

        token_heap = []

        for token_type, pattern_str in patterns:
            pattern = re.compile(pattern_str)
            match = pattern.search(text)

            if match is None:
                continue

            print(pattern, match.start())
            token_heap.append(Token(match.start(), token_type, match, pattern))

        heapq.heapify(token_heap)

        self.token_heap = token_heap

    def tokenize(self) -> t.Generator[t.Tuple[TokenType, re.Match], None, None]:
        iters = 0
        prev_end_loc = -1
        while self.token_heap:
            iters += 1
            if iters > 100:
                raise Exception

            start_loc, token_type, match_obj, pattern = heapq.heappop(self.token_heap)

            # If overlaps with something already seen, we should skip.
            if start_loc >= prev_end_loc:
                yield token_type, match_obj

            end_loc = match_obj.end()
            prev_end_loc = max(end_loc, prev_end_loc)
            next_match = pattern.search(self.text, end_loc)

            # If match is none, this pattern doesn't appear in the text anymore, so we
            # can just throw away.
            if next_match is not None:
                heapq.heappush(
                    self.token_heap,
                    Token(next_match.start(), token_type, next_match, pattern),
                )


class Lexer:
    """
    The core lexer.
    """

    # __slots__: Tuple[str, ...] = ("tokens", "blank_chars")

    def __init__(self, text: str) -> None:
        token_patterns = [
            (TokenType.RAW_VARIABLE, r"\{\{\{"),
            (TokenType.VARIABLE, r"\{\{(.*?)\}\}"),
        ]
        self.tokens = MustacheTokenizer(text, token_patterns)
        # self.blank_chars = (
        #    frozenset((" ", "\t")) if blank_chars is None else frozenset(blank_chars)
        # )

    def tokenize(self):
        for token_type, token_data in self.tokens.tokenize():
            print(token_type, token_data)
