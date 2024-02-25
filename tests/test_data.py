import io
from pathlib import Path

from chevron2.main import main


def test_main(datadir: Path) -> None:
    mustache_path = datadir / "test.mustache"
    data_path = datadir / "data.json"

    result = main(mustache_path, data_path, partials_path=datadir)

    expected_path = datadir / "test.rendered"
    with io.open(expected_path, "r", encoding="utf-8") as f:
        expected = f.read()

    assert result == expected
