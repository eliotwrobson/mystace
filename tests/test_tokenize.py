from chevron2 import render_from_template


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
    data = {"thing": {"inner_thing": True}}

    val = render_from_template(template, data)
    print("res:", val)
    assert False
