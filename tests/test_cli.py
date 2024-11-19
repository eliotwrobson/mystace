# import io
from pathlib import Path

# from mystace import render
# https://github.com/sakhezech/combustache/blob/main/src/combustache/__main__.py


def test_main(datadir: Path) -> None:
    pass
    # TODO add back the ability to read paths
    # mustache_path = datadir / "test.mustache"
    # data_path = datadir / "data.json"

    # result = render(mustache_path, data_path, partials_path=datadir)

    # expected_path = datadir / "test.rendered"
    # with io.open(expected_path, "r", encoding="utf-8") as f:
    #     expected = f.read()

    # assert result == expected
