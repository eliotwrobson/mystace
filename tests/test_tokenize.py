from chevron2 import mustache_tokenizer, render_from_template


def test_lexer() -> None:
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

    thing = mustache_tokenizer(template)
    for item in thing:
        print(item)
    assert False


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
    data = {"a": {"b": {"c": {"name": "stuff"}}}, "c": {"name": "Jim"}}
    template = '"{{a.b.c.name}}" == ""'
    expected = '"stuff" == ""'

    val = render_from_template(template, data)
    print(val)

    assert False
