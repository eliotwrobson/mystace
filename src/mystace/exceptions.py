# https://github.com/michaelrccurtis/moosetash/blob/main/moosetash/handlers.py
# https://github.com/michaelrccurtis/moosetash/blob/main/moosetash/exceptions.py


class MystaceError(Exception):
    """
    Mystace base exception. Not raised.
    """

    pass


class NodeHasNoChildren(MystaceError):
    """
    Tried to access children of a MustacheTreeNode type that does not
    have any.
    """

    pass


class DelimiterError(MystaceError):
    """
    A delimiter tag contents are wrong.
    """

    pass


class MissingClosingTagError(MystaceError):
    """
    A closing tag for an opened tag is not found.
    """

    pass


class StrayClosingTagError(MystaceError):
    """
    A closing tag for an unopened tag is found.
    """

    pass
