from chevron2.nodes.node import Node


class Comment(Node):
    left = "!"
    ignorable = True
