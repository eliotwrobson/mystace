import chevron2.main
from chevron2.ctx import MISSING, Ctx
from chevron2.exceptions import MissingClosingTagError, StrayClosingTagError
from chevron2.nodes.node import Node
from chevron2.util import LAMBDA, is_callable


class Section(Node):
    left = "#"

    def find_closing(self):
        depth = 0
        search_start = self.end
        while True:
            node_info = chevron2.main.find_node(
                self.template,
                search_start,
                self.template_end,
                self.left_delimiter,
                self.right_delimiter,
            )
            if node_info is None:
                raise MissingClosingTagError(
                    "No closing tag found for " f"{self.presentable} at {self.start}."
                )

            content, start, end = node_info
            if (
                content[0] == self.left
                and content.removeprefix(self.left).strip() == self.content
            ):
                depth += 1
            elif (
                content[0] == "/" and content.removeprefix("/").strip() == self.content
            ):
                if depth == 0:
                    break
                depth -= 1
            search_start = end
        return content, start, end

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

        content, start, end = self.find_closing()
        # not creating ClosingTag because it raises the stray tag error
        closing_tag = Node(
            content,
            start,
            end,
            self.template,
            self.template_start,
            self.template_end,
            self.left_delimiter,
            self.right_delimiter,
        )

        self.inside_start = self.end
        self.inside_end = closing_tag.start
        self.parse_end = closing_tag.end
        self.inside = chevron2.main.parse(
            self.template,
            self.inside_start,
            self.inside_end,
            self.left_delimiter,
            self.right_delimiter,
        )

    def should_be_rendered(self, item):
        return item and item is not MISSING

    def handle(self, ctx: Ctx, partials: dict, opts: dict) -> str:
        missing_data = opts["missing_data"]

        data = ctx.get(self.content)

        if not self.should_be_rendered(data):
            if data is MISSING:
                return missing_data()
            return ""

        if is_callable(data):
            unprocessed = self.template[self.inside_start : self.inside_end]
            if data.__name__ == LAMBDA:
                template = str(data(unprocessed))
                return chevron2.main._render(
                    template,
                    ctx,
                    partials,
                    opts,
                    self.left_delimiter,
                    self.right_delimiter,
                )
            else:
                try:
                    data = data(unprocessed)
                except TypeError:
                    data = data()

        # if data is not a list we put it into one
        # so we can process it easily
        if not isinstance(data, list) or not data:
            data = [data]

        handled = []
        for item in data:
            ctx.append(item)
            handled.extend(
                [
                    node.handle(ctx, partials, opts) if isinstance(node, Node) else node
                    for node in self.inside
                ]
            )
            ctx.pop()
        return "".join(handled)


class Inverted(Section):
    left = "^"

    def should_be_rendered(self, item):
        return not item or item is MISSING


class Closing(Node):
    left = "/"
    ignorable = True

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        raise StrayClosingTagError(
            f"Stray closing tag found {self.presentable} at {self.start}."
        )
