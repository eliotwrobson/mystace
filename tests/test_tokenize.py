from chevron2 import tokenize


def test_split_into_sub_tokens() -> None:
    thing = r"A{{#x}}B{{#x}}{{.}}{{/x}}C{{/x}}D"
    data = {"x": ["z", "x"]}
    res = tokenize(thing, data)
    print(res)
    assert False
