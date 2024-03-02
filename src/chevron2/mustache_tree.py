import enum

# '!': 'comment',
# '#': 'section',
# '^': 'inverted section',
# '/': 'end',
# '>': 'partial',
# '=': 'set delimiter?',
# '{': 'no escape?',
# '&': 'no escape'

class TagType(enum.Enum):
    COMMENT = 1
    SECTION = 2
    INVERTED_SECTION = 3
    END_SECTION = 4
    PARTIAL = 5


class MustacheTreeNode:


def create_mustache_tree(thing:str) -> MustacheTreeNode:
