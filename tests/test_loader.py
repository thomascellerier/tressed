import pytest

from gluetypes.loader import Loader
from gluetypes.exceptions import GluetypesTypeError, GluetypesValueError


def test_load_simple_types() -> None:
    loader = Loader()
    assert loader.load(1, int) == 1
    assert loader.load(1.1, float) == 1.1
    assert loader.load(True, bool) is True
    assert loader.load(False, bool) is False
    assert loader.load("foo", str) == "foo"
    assert loader.load(None, type(None)) is None

    with pytest.raises(GluetypesValueError):
        loader.load(1, str)


def test_load_unknown_type() -> None:
    loader = Loader()

    class MadeupType:
        pass

    with pytest.raises(GluetypesTypeError):
        loader.load(1, MadeupType)
