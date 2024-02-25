class Chevron2Error(Exception):
    """
    Chevron2 base exception. Not raised.
    """

    pass


class DelimiterError(Chevron2Error):
    """
    A delimiter tag contents are wrong.
    """

    pass


class MissingClosingTagError(Chevron2Error):
    """
    A closing tag for an opened tag is not found.
    """

    pass


class StrayClosingTagError(Chevron2Error):
    """
    A closing tag for an unopened tag is found.
    """

    pass
