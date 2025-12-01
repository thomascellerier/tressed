import gc
import sys
from typing import NewType, assert_type
from unittest.mock import call

import pytest
from pytest_benchmark.fixture import BenchmarkFixture
from pytest_mock import MockerFixture

from tressed.exceptions import TressedTypeError, TressedValueError
from tressed.loader import Loader


def test_load_identity() -> None:
    loader = Loader()
    assert loader.load(1, int) == 1
    assert loader.load(1.1, float) == 1.1
    assert loader.load(True, bool) is True
    assert loader.load(False, bool) is False
    assert loader.load("foo", str) == "foo"
    assert loader.load(None, type(None)) is None

    with pytest.raises(TressedValueError):
        loader.load(1, str)


def test_load_list() -> None:
    loader = Loader()
    assert loader.load([1, 2, 3], list[int]) == [1, 2, 3]

    with pytest.raises(TressedTypeError):
        loader.load(["foo", "bar"], list)

    with pytest.raises(TressedValueError):
        loader.load(["foo", "bar"], list[int])


def test_load_set() -> None:
    loader = Loader()
    loaded = loader.load([1, 2, 3, 2], set[int])
    assert type(loaded) is set
    assert loaded == {1, 2, 3}

    with pytest.raises(TressedTypeError):
        loader.load(["foo", "bar"], set)

    with pytest.raises(TressedValueError):
        loader.load(["foo", "bar"], set[int])


def test_load_frozenset() -> None:
    loader = Loader()
    loaded = loader.load([1, 2, 3, 2], frozenset[int])
    assert type(loaded) is frozenset
    assert loaded == frozenset({1, 2, 3})

    with pytest.raises(TressedTypeError):
        loader.load(["foo", "bar"], frozenset)

    with pytest.raises(TressedValueError):
        loader.load(["foo", "bar"], frozenset[int])


def test_load_homogeneous_tuple() -> None:
    loader = Loader()
    assert loader.load([1, 2, 3], tuple[int, ...]) == (1, 2, 3)

    with pytest.raises(TressedTypeError):
        loader.load(["foo", "bar"], tuple)

    with pytest.raises(TressedValueError):
        loader.load(["foo", "bar"], tuple[int, ...])


def test_load_tuple() -> None:
    loader = Loader()
    assert loader.load([], tuple[()]) == ()
    assert loader.load([1], tuple[int]) == (1,)
    assert loader.load([1, True], tuple[int, bool]) == (1, True)
    assert loader.load([1, True, 1.1], tuple[int, bool, float]) == (1, True, 1.1)

    with pytest.raises(TressedValueError):
        loader.load([1, True, "foo"], tuple[int, bool, float])


def test_load_newtype() -> None:
    T = NewType("T", int)

    loader = Loader()
    loaded = loader.load(123, T)
    assert_type(loaded, T)

    assert loaded == T(123)


def test_load_ipaddress() -> None:
    import ipaddress

    loader = Loader()
    loaded = loader.load("127.0.0.1", ipaddress.IPv4Address)
    assert_type(loaded, ipaddress.IPv4Address)


def test_load_tuple_benchmark(benchmark: BenchmarkFixture) -> None:
    loader = Loader()
    benchmark(loader.load, [1, True, 1.1], tuple[int, bool, float])


def test_load_tuple_specialized_benchmark(benchmark: BenchmarkFixture) -> None:
    loader = Loader(enable_specialization=True)
    benchmark(loader.load, [1, True, 1.1], tuple[int, bool, float])


def test_load_set_benchmark(benchmark: BenchmarkFixture) -> None:
    loader = Loader()
    benchmark(loader.load, [[1, "two", 3.3]] * 30, set[tuple[int, str, float]])


def test_load_set_specialized_benchmark(benchmark: BenchmarkFixture) -> None:
    loader = Loader(enable_specialization=True)
    benchmark(loader.load, [[1, "two", 3.3]] * 30, set[tuple[int, str, float]])


def test_load_unknown_type() -> None:
    # Loading an unknown type will go through all the predicates,
    # make sure the predicates do not load any additional modules.
    if "dataclasses" in sys.modules:
        del sys.modules["dataclasses"]
        gc.collect()

    modules_before = frozenset(sys.modules.keys())
    assert "dataclasses" not in modules_before

    loader = Loader()

    class MadeupType:
        pass

    with pytest.raises(TressedTypeError):
        loader.load(1, MadeupType)

    modules_after = frozenset(sys.modules.keys())
    new_modules = frozenset(
        {
            module
            for module in modules_after - modules_after
            # Ignore internal modules
            if not module.startswith("tressed.")
        }
    )
    assert new_modules == frozenset()


def test_load_dataclass(mocker: MockerFixture) -> None:
    from dataclasses import dataclass, field

    @dataclass
    class SomeDataclass:
        foo: str
        bar: str = "bar"
        baz: list[int] = field(default_factory=lambda: [1, 2, 3])
        bar_bar: tuple[int, str] = field(metadata={"alias": "barBar"}, kw_only=True)

    value = {
        "foo": "foo",
        "barBar": (2, "humbug"),
    }
    expected = SomeDataclass(
        foo="foo",
        bar="bar",
        baz=[1, 2, 3],
        bar_bar=(2, "humbug"),
    )
    expected_cache = {
        (SomeDataclass, (), "foo"): "foo",
        (SomeDataclass, (), "bar"): "bar",
        (SomeDataclass, (), "baz"): "baz",
        (SomeDataclass, (), "bar_bar"): "barBar",
    }

    loader = Loader()

    spy_resolve_alias = mocker.spy(loader, loader._resolve_alias.__name__)
    spy_resolve_alias_no_cache = mocker.spy(
        loader, loader._resolve_alias_no_cache.__name__
    )

    assert loader.load(value, SomeDataclass) == expected

    # First, call make sure that the cache is created
    assert loader._alias_cache == expected_cache

    expected_calls = [
        call(SomeDataclass, (), "foo"),
        call(SomeDataclass, (), "bar"),
        call(SomeDataclass, (), "baz"),
        call(SomeDataclass, (), "bar_bar"),
    ]
    assert spy_resolve_alias.call_args_list == expected_calls
    assert spy_resolve_alias_no_cache.call_args_list == expected_calls

    assert loader.load(value, SomeDataclass) == expected

    # Second, call make sure that the cache is used created
    assert loader._alias_cache == expected_cache
    assert spy_resolve_alias.call_args_list == expected_calls * 2
    assert spy_resolve_alias_no_cache.call_args_list == expected_calls
