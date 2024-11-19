from mystace.tokenize import mustache_tokenizer


def test_tokenize() -> None:
    # TODO figure out what the original purpose of this was.
    n = 10
    names = {f"thing{i}": i for i in range(n)}
    template = "".join(R"{{" + name + R"}}" for name in names.keys())

    res = mustache_tokenizer(template)
    print(res)
    # print(mustache_tokenizer("aoe{{stuff}}uaoeu{{#thing}}a\noeua"))
