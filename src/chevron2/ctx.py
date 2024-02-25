from typing import Any

MISSING = object()


class Ctx(list):
    """
    Context stack.
    """

    def get(self, key: str) -> Any:
        if key == '.':
            return self[-1]

        chain = key.split('.')
        reversed_ctx = reversed(self)

        found = MISSING
        for item in reversed_ctx:
            found = deep_get(item, chain[0])
            if found is not MISSING:
                break

        if found is MISSING:
            return MISSING

        for key in chain[1:]:
            found = deep_get(found, key)
        return found


def deep_get(item: Any, key: str) -> Any:
    try:
        item = item()
    except TypeError:
        pass

    try:
        try:
            return item[key]
        except KeyError:
            return MISSING
    except TypeError:
        pass

    try:
        idx = int(key)
        try:
            return item[idx]
        except IndexError:
            return MISSING
    except ValueError:
        pass

    return getattr(item, key, MISSING)
