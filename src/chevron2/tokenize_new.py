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
    VARIABLE = 1


class Token(t.NamedTuple):
    loc: int
    type: TokenType
    next_match: re.Match[str]
    pattern: re.Pattern


class TokenRegistry:
    """A registry which yields matches for the given tokens over a single corpus."""

    # __slots__: t.Tuple[str, ...] = ("_tokens",)

    token_heap: t.List[Token]

    def __init__(self, text: str, patterns: t.Dict[TokenType, str]) -> None:
        token_heap = []

        for token_type, pattern_str in patterns.items():
            pattern = re.compile(pattern_str)
            match = pattern.search(text)

            if match is None:
                continue

            print(pattern, match.start())
            token_heap.append(Token(match.start(), token_type, match, pattern))

        heapq.heapify(token_heap)

        self.token_heap = token_heap

        print(token_heap)


class Lexer:
    """
    The core lexer.
    """

    # __slots__: Tuple[str, ...] = ("tokens", "blank_chars")

    def __init__(self, text: str) -> None:
        token_patterns = {TokenType.VARIABLE: r"\{\{"}
        self.tokens = TokenRegistry(text, token_patterns)
        # self.blank_chars = (
        #    frozenset((" ", "\t")) if blank_chars is None else frozenset(blank_chars)
        # )
