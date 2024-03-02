from chevron2 import create_mustache_tree


def test_tokenize() -> None:
    template = """
        {{#thing}}
        hello
        {{/thing}}
    """
    res = create_mustache_tree(template)
    print(res)

    assert False
