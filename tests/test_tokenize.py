from chevron2 import tokenize


def test_split_into_sub_tokens() -> None:
    thing = r"A{{#x}}B{{#x}}{{.}}{{/x}}C{{/x}}D"
    res = tokenize(thing)
    print(res)
    assert False
