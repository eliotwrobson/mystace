import chevron2.main
from chevron2.ctx import Ctx
from chevron2.nodes.node import Node


class Partial(Node):
    left = ">"

    def handle(self, ctx: Ctx, partials: dict, opts: dict) -> str:
        missing_data = opts["missing_data"]

        partial_template = partials.get(self.content)

        if partial_template is None:
            return missing_data()

        partial_lines = partial_template.split("\n")
        if self.is_standalone:
            stack = [
                bool(line) * self.before
                + chevron2.main._render(line, ctx, partials, opts)
                for line in partial_lines
            ]
        else:
            stack = [
                chevron2.main._render(line, ctx, partials, opts)
                for line in partial_lines
            ]
        return "\n".join(stack)
