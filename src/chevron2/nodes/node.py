from chevron2.ctx import Ctx
from chevron2.util import is_whitespace


class Node:
    left = ""
    right = ""
    ignorable = False
    standalonable = True

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
        self.template = template
        self.template_start = template_start
        self.template_end = template_end
        self.left_delimiter = left_delimiter
        self.right_delimiter = right_delimiter
        self.inside: list[str | Node] = []

        # we +1 to line_start and line_end to get 'hello\n' instad of '\nhello'
        # and we get a nice side effect for end of getting 0 if we dont find \n
        # (i.e. we hit end of string) because str.find returns -1 in that case
        # so we can 'or len(template)' our value to get the end of the template
        line_start = template.rfind("\n", 0, tag_start) + 1
        line_end = template.find("\n", tag_end) + 1 or len(template)

        self.before = template[line_start:tag_start]
        self.after = template[tag_end:line_end]

        self.is_standalone = is_whitespace(self.before) and is_whitespace(self.after)
        if self.standalonable and self.is_standalone:
            self.start = line_start
            self.end = line_end
        else:
            self.start = tag_start
            self.end = tag_end
        self.parse_end = self.end

        self.content = content.removeprefix(self.left).removesuffix(self.right).strip()

    @property
    def presentable(self) -> str:
        return (
            f"{self.left_delimiter}{self.left}"
            f"{self.content}{self.right}{self.right_delimiter}"
        )

    def handle(self, ctx: Ctx, partials: dict, opts: dict) -> str:
        raise NotImplementedError
