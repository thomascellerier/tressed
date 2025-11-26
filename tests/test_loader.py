import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from gluetypes.loader import Loader
from gluetypes.exceptions import GluetypesTypeError, GluetypesValueError


def test_load_simple_scalar() -> None:
    loader = Loader()
    assert loader.load(1, int) == 1
    assert loader.load(1.1, float) == 1.1
    assert loader.load(True, bool) is True
    assert loader.load(False, bool) is False
    assert loader.load("foo", str) == "foo"
    assert loader.load(None, type(None)) is None

    with pytest.raises(GluetypesValueError):
        loader.load(1, str)


def test_load_list() -> None:
    loader = Loader()
    assert loader.load([1, 2, 3], list[int]) == [1, 2, 3]

    with pytest.raises(GluetypesTypeError):
        loader.load(["foo", "bar"], list)

    with pytest.raises(GluetypesValueError):
        loader.load(["foo", "bar"], list[int])


def test_load_set() -> None:
    loader = Loader()
    loaded = loader.load([1, 2, 3, 2], set[int])
    assert type(loaded) is set
    assert loaded == {1, 2, 3}

    with pytest.raises(GluetypesTypeError):
        loader.load(["foo", "bar"], set)

    with pytest.raises(GluetypesValueError):
        loader.load(["foo", "bar"], set[int])


def test_load_frozenset() -> None:
    loader = Loader()
    loaded = loader.load([1, 2, 3, 2], frozenset[int])
    assert type(loaded) is frozenset
    assert loaded == frozenset({1, 2, 3})

    with pytest.raises(GluetypesTypeError):
        loader.load(["foo", "bar"], frozenset)

    with pytest.raises(GluetypesValueError):
        loader.load(["foo", "bar"], frozenset[int])


def test_load_homogeneous_tuple() -> None:
    loader = Loader()
    assert loader.load([1, 2, 3], tuple[int, ...]) == (1, 2, 3)

    with pytest.raises(GluetypesTypeError):
        loader.load(["foo", "bar"], tuple)

    with pytest.raises(GluetypesValueError):
        loader.load(["foo", "bar"], tuple[int, ...])


def test_load_tuple() -> None:
    loader = Loader()
    assert loader.load([], tuple[()]) == ()
    assert loader.load([1], tuple[int]) == (1,)
    assert loader.load([1, True], tuple[int, bool]) == (1, True)
    assert loader.load([1, True, 1.1], tuple[int, bool, float]) == (1, True, 1.1)

    with pytest.raises(GluetypesValueError):
        loader.load([1, True, "foo"], tuple[int, bool, float])


def test_load_tuple_benchmark(benchmark: BenchmarkFixture) -> None:
    loader = Loader()
    benchmark(loader.load, [1, True, 1.1], tuple[int, bool, float])


def test_load_tuple_specialized_benchmark(benchmark: BenchmarkFixture) -> None:
    loader = Loader(enable_specialization=True)
    benchmark(loader.load, [1, True, 1.1], tuple[int, bool, float])


def test_load_unknown_type() -> None:
    loader = Loader()

    class MadeupType:
        pass

    with pytest.raises(GluetypesTypeError):
        loader.load(1, MadeupType)
