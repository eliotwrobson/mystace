from combustache.exceptions import DelimiterError
from combustache.nodes.node import Node


class Delimiter(Node):
    left = '='
    right = '='
    ignorable = True

    def __init__(
        self,
        content: str,
        tag_start: int,
        tag_end: int,
        template: str,
        template_start: int,
        template_end: int,
        left_delimiter: str,
        right_delimiter: str,
    ) -> None:
        super().__init__(
            content,
            tag_start,
            tag_end,
            template,
            template_start,
            template_end,
            left_delimiter,
            right_delimiter,
        )
        split = self.content.split()
        if len(split) != 2:
            raise DelimiterError(
                'Impossible delimiter tag found '
                f'{self.presentable} at {self.start}.'
            )
        self.left_delimiter = split[0]
        self.right_delimiter = split[1]
