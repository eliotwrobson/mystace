
import chevron2
import chevron
import random

def test_large() -> None:
    n = 10_000

    names = {
        f"thing{i}": i
        for i in range(n)
    }

    template = "".join(r"{{" + name + "}}" for name in names.keys())


    import time
    start = time.perf_counter()
    chevron.render(template, names)
    end = time.perf_counter()
    print(end-start)
    assert False
