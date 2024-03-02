from chevron2 import create_mustache_tree


def test_tokenize() -> None:
    template = """
        {{! random comment }}
        {{#thing}}
            {{#inner_thing}}
            hello
            {{/inner_thing}}
            {{outer_thing}}
        {{/thing}}
        {{^other.thing}}
            {{{another_name}}}
        {{/other.thing}}
    """
    res = create_mustache_tree(template)
    print(res)

    assert False
