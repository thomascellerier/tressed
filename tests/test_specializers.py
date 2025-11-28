def test_specialize_load_tuple() -> None:
    from gluetypes.loader import Loader
    from gluetypes.loader.specializers import specialize_load_tuple

    code = specialize_load_tuple(tuple[int, float, str], ("foo", 1))
    assert (
        code
        == """\
def __specialized_fn(value, loader):
    _item_0, _item_1, _item_2 = value
    _load = loader._load
    _item_0_loaded = _load(_item_0, int, ('foo', 1, 0))
    _item_1_loaded = _load(_item_1, float, ('foo', 1, 1))
    _item_2_loaded = _load(_item_2, str, ('foo', 1, 2))
    return (
        _item_0_loaded,
        _item_1_loaded,
        _item_2_loaded,
    )

"""
    )
    loader = Loader()
    globals_ = {}
    locals_ = {}
    exec(code, globals_, locals_)
    specialized_fn = locals_["__specialized_fn"]
    assert specialized_fn([1, 1.1, "foobar"], loader) == (1, 1.1, "foobar")


def test_specialize_load_simple_collection() -> None:
    from gluetypes.loader import Loader
    from gluetypes.loader.specializers import specialize_load_simple_collection

    code = specialize_load_simple_collection(
        set[tuple[int, str, float]], ("foo", 0, "bar")
    )
    assert (
        code
        == """\
def __specialized_fn(value, loader):
    _load = loader._load
    return {
        _load(item, tuple[int, str, float], ('foo', 0, 'bar', pos))
        for pos, item
        in enumerate(value)
    }

"""
    )
    loader = Loader()
    globals_ = {}
    locals_ = {}
    exec(code, globals_, locals_)
    specialized_fn = locals_["__specialized_fn"]
    assert specialized_fn(
        [[1, "two", 3.3], [4, "five", 5.5], [1, "two", 3.3]], loader
    ) == {(1, "two", 3.3), (4, "five", 5.5)}
