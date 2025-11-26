def test_specialize_load_tuple() -> None:
    from gluetypes.loader import Loader
    from gluetypes.loader.specializers import specialize_load_tuple

    code = specialize_load_tuple(tuple[int, float, str], ("foo", 1))
    assert (
        code
        == """\
def __specialized_fn(value, loader):
    item_0, item_1, item_2 = value
    _load = loader._load
    return (
        _load(item_0, int, ('foo', 1, 0)),
        _load(item_1, float, ('foo', 1, 1)),
        _load(item_2, str, ('foo', 1, 2)),
    )

"""
    )
    loader = Loader()
    globals_ = {}
    locals_ = {}
    exec(code, globals_, locals_)
    specialized_fn = locals_["__specialized_fn"]
    assert specialized_fn([1, 1.1, "foobar"], loader) == (1, 1.1, "foobar")
