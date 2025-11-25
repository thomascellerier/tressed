def test_import_gluetypes() -> None:
    import gluetypes

    assert list(map(str, dir(gluetypes))) == [
        "__builtins__",
        "__cached__",
        "__doc__",
        "__file__",
        "__loader__",
        "__name__",
        "__package__",
        "__path__",
        "__spec__",
    ]
