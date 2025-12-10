import gc
import sys
from typing import NewType, assert_type

import pytest
from pytest_benchmark.fixture import BenchmarkFixture
from pytest_mock import MockerFixture

from tressed.exceptions import (
    TressedTypeFormError,
    TressedValueError,
)
from tressed.loader import Loader

TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import Any

    from tressed.type_form import TypeForm


def test_load_identity() -> None:
    loader = Loader()
    assert loader.load(1, int) == 1
    assert loader.load(True, bool) is True
    assert loader.load(False, bool) is False
    assert loader.load("foo", str) == "foo"
    assert loader.load(None, type(None)) is None

    with pytest.raises(TressedValueError):
        loader.load(1, str)


def test_load_float() -> None:
    loader = Loader()

    assert loader.load(1.1, float) == 1.1
    assert loader.load(1, float) == 1.0


def test_load_complex() -> None:
    loader = Loader()

    loader.load([1.1, 2.2], complex) == 1.1 + 2.2j
    loader.load([1, 2.2], complex) == 1 + 2.2j
    loader.load([1.1, 2], complex) == 1.1 + 2j
    loader.load([1, 2], complex) == 1 + 2j


def test_load_list() -> None:
    loader = Loader()
    assert loader.load([1, 2, 3], list[int]) == [1, 2, 3]

    with pytest.raises(TressedTypeFormError):
        loader.load(["foo", "bar"], list)

    with pytest.raises(TressedValueError):
        loader.load(["foo", "bar"], list[int])


def test_load_set() -> None:
    loader = Loader()
    loaded = loader.load([1, 2, 3, 2], set[int])
    assert type(loaded) is set
    assert loaded == {1, 2, 3}

    with pytest.raises(TressedTypeFormError):
        loader.load(["foo", "bar"], set)

    with pytest.raises(TressedValueError):
        loader.load(["foo", "bar"], set[int])


def test_load_frozenset() -> None:
    loader = Loader()
    loaded = loader.load([1, 2, 3, 2], frozenset[int])
    assert type(loaded) is frozenset
    assert loaded == frozenset({1, 2, 3})

    with pytest.raises(TressedTypeFormError):
        loader.load(["foo", "bar"], frozenset)

    with pytest.raises(TressedValueError):
        loader.load(["foo", "bar"], frozenset[int])


def test_load_homogeneous_tuple() -> None:
    loader = Loader()
    assert loader.load([1, 2, 3], tuple[int, ...]) == (1, 2, 3)

    with pytest.raises(TressedTypeFormError):
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
    loaded_v4a = loader.load("127.0.0.1", ipaddress.IPv4Address)
    assert_type(loaded_v4a, ipaddress.IPv4Address)

    loaded_v6a = loader.load("::1", ipaddress.IPv6Address)
    assert_type(loaded_v6a, ipaddress.IPv6Address)

    loaded_v4n = loader.load("127.0.0.0/24", ipaddress.IPv4Network)
    assert_type(loaded_v4n, ipaddress.IPv4Network)

    loaded_v6n = loader.load("::0/64", ipaddress.IPv6Network)
    assert_type(loaded_v6n, ipaddress.IPv6Network)

    loaded_v4i = loader.load("127.0.0.1/24", ipaddress.IPv4Interface)
    assert_type(loaded_v4i, ipaddress.IPv4Interface)

    loaded_v6i = loader.load("::1/64", ipaddress.IPv6Interface)
    assert_type(loaded_v6i, ipaddress.IPv6Interface)


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

    with pytest.raises(TressedTypeFormError):
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
    loader = Loader()
    assert loader.load(value, SomeDataclass) == expected

    assert loader._alias_resolver._cache == {
        ("foo", SomeDataclass, ()): "foo",
        ("bar", SomeDataclass, ()): "bar",
        ("baz", SomeDataclass, ()): "baz",
        ("bar_bar", SomeDataclass, ()): "barBar",
    }


def test_load_dataclass_caching_enabled(mocker: MockerFixture) -> None:
    from dataclasses import dataclass, field

    @dataclass
    class SomeDataclass:
        foo: str
        bar: str = "bar"
        baz: list[int] = field(default_factory=lambda: [1, 2, 3])
        bar_bar: tuple[int, str] = field(metadata={"alias": "barBar"}, kw_only=True)

    count = 0

    def _count_alias_fn(name: str) -> str:
        nonlocal count
        count += 1
        return name

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
    loader = Loader(alias_fn=_count_alias_fn)
    assert loader.load(value, SomeDataclass) == expected
    assert count == 3

    assert loader.load(value, SomeDataclass) == expected
    assert count == 3


def test_load_dataclass_caching_disabled(mocker: MockerFixture) -> None:
    from dataclasses import dataclass, field

    from tressed.alias import AliasResolver

    @dataclass
    class SomeDataclass:
        foo: str
        bar: str = "bar"
        baz: list[int] = field(default_factory=lambda: [1, 2, 3])
        bar_bar: tuple[int, str] = field(metadata={"alias": "barBar"}, kw_only=True)

    count = 0

    def _count_alias_fn(name: str) -> str:
        nonlocal count
        count += 1
        return name

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
    loader = Loader(
        alias_fn=_count_alias_fn,
        alias_resolver_factory=lambda alias_fn: AliasResolver(
            alias_fn, cache_resolved_aliases=False
        ),
    )
    assert loader.load(value, SomeDataclass) == expected
    assert count == 3
    assert loader._alias_resolver._cache == {}

    assert loader.load(value, SomeDataclass) == expected
    assert count == 6
    assert loader._alias_resolver._cache == {}


def test_load_dataclass_alias_fn(mocker: MockerFixture) -> None:
    from dataclasses import dataclass, field

    from tressed.alias import to_camel

    @dataclass
    class SomeDataclass:
        foo_foo: str
        baz_baz: list[int] = field(default_factory=lambda: [1, 2, 3])
        bar_bar: tuple[int, str] = field(metadata={"alias": "BAR_BAR"}, kw_only=True)

    value = {
        "fooFoo": "foo",
        "BAR_BAR": (2, "humbug"),
    }
    expected = SomeDataclass(
        foo_foo="foo",
        baz_baz=[1, 2, 3],
        bar_bar=(2, "humbug"),
    )
    loader = Loader(alias_fn=to_camel)
    assert loader.load(value, SomeDataclass) == expected
    assert loader._alias_resolver._cache == {
        ("foo_foo", SomeDataclass, ()): "fooFoo",
        ("baz_baz", SomeDataclass, ()): "bazBaz",
        ("bar_bar", SomeDataclass, ()): "BAR_BAR",
    }


def test_load_dict() -> None:
    loader = Loader()

    loaded = loader.load({"foo": [1, 2], "bar": [5, 6, 6, 8]}, dict[str, set[int]])
    assert_type(loaded, dict[str, set[int]])
    assert loaded == {
        "foo": {1, 2},
        "bar": {5, 6, 8},
    }


def test_load_legacy_dict() -> None:
    from typing import Dict

    loader = Loader()

    loaded = loader.load({"foo": [1, 2], "bar": [5, 6, 6, 8]}, Dict[str, set[int]])
    assert_type(loaded, dict[str, set[int]])
    assert loaded == {
        "foo": {1, 2},
        "bar": {5, 6, 8},
    }


def test_load_typeddict() -> None:
    from typing import TypedDict

    loader = Loader()

    class SomeTypedDict(TypedDict):
        foo: int
        bar: str

    loaded = loader.load({"foo": 123, "bar": "BAR"}, SomeTypedDict)
    assert_type(loaded, SomeTypedDict)
    assert loaded == {"foo": 123, "bar": "BAR"}


def test_load_typeddict_optional_keys() -> None:
    from typing import TypedDict

    loader = Loader()

    class SomeTypedDict(TypedDict, total=False):
        foo: int
        bar: str

    loaded = loader.load({"foo": 123}, SomeTypedDict)
    assert_type(loaded, SomeTypedDict)
    assert loaded == {"foo": 123}

    loaded = loader.load({"foo": 123, "bar": "BAR", "baz": "BAZ"}, SomeTypedDict)
    assert_type(loaded, SomeTypedDict)
    assert loaded == {"foo": 123, "bar": "BAR", "baz": "BAZ"}


def test_load_typeddict_closed() -> None:
    from typing_extensions import TypedDict

    loader = Loader()

    class SomeTypedDict(TypedDict, closed=True):  # type: ignore[call-arg]
        foo: int

    with pytest.raises(TressedValueError) as exc_info:
        loader.load(
            {"foo": 123, "bar": "bar", "buz": "BUZ", "baz": "BAZ"}, SomeTypedDict
        )

    assert str(exc_info.value) == (
        "Failed to load value of type dict at path . into type form SomeTypedDict: "
        "extra keys 'bar', 'baz', 'buz': {'foo': 123, 'bar': 'bar', 'buz': 'BUZ', 'baz': 'BAZ'}"
    )


def test_load_typeddict_extra_items() -> None:
    from typing_extensions import TypedDict

    loader = Loader()

    class SomeTypedDict(TypedDict, extra_items=str):  # type: ignore[call-arg]
        foo: int
        bar: str
        baz: str

    loaded = loader.load(
        {"foo": 123, "bar": "bar", "buz": "BUZ", "baz": "BAZ"}, SomeTypedDict
    )
    assert_type(loaded, SomeTypedDict)
    assert loaded == {"foo": 123, "bar": "bar", "buz": "BUZ", "baz": "BAZ"}


def test_load_namedtuple() -> None:
    from typing import NamedTuple

    class SomeNamedTuple(NamedTuple):
        foo: tuple[int, float]
        bar: str = "bar"

    loader = Loader()
    assert loader.load(
        {"foo": [1, 1.1], "bar": "BAR!"}, SomeNamedTuple
    ) == SomeNamedTuple(foo=(1, 1.1), bar="BAR!")
    assert loader.load({"foo": [1, 1.1]}, SomeNamedTuple) == SomeNamedTuple(
        foo=(1, 1.1), bar="bar"
    )

    with pytest.raises(TressedValueError):
        assert loader.load(
            {"foo": [1, 1.1], "baz": "baz"}, SomeNamedTuple
        ) == SomeNamedTuple(foo=(1, 1.1), bar="bar")
    with pytest.raises(TressedValueError):
        assert loader.load({"bar": "BAR!"}, SomeNamedTuple) == SomeNamedTuple(
            foo=(1, 1.1), bar="BAR!"
        )


def test_load_from_argparse_namespace() -> None:
    from argparse import Namespace
    from typing import NamedTuple

    class SomeNamedTuple(NamedTuple):
        foo: tuple[int, float]
        bar: str = "bar"

    loader = Loader()
    assert loader.load(
        Namespace(foo=[1, 1.1], bar="BAR!"), SomeNamedTuple
    ) == SomeNamedTuple(foo=(1, 1.1), bar="BAR!")


def test_load_enum() -> None:
    from enum import Enum, IntEnum, StrEnum, auto

    class SomeEnum(Enum):
        FOO = "foo"
        BAR = "bar"

    loader = Loader()
    assert loader.load("foo", SomeEnum) == SomeEnum.FOO

    class SomeStrEnum(StrEnum):
        FOO = auto()
        BAR = auto()

    assert loader.load("bar", SomeStrEnum) == SomeStrEnum.BAR

    class SomeIntEnum(IntEnum):
        FOO = auto()
        BAR = auto()

    assert loader.load(1, SomeIntEnum) == SomeIntEnum.FOO


def test_load_uuid() -> None:
    import uuid

    loader = Loader()

    # uuid1
    assert loader.load("417c0ae2-d114-11f0-b300-d7c04d362c1f", uuid.UUID) == uuid.UUID(
        "417c0ae2-d114-11f0-b300-d7c04d362c1f"
    )
    # uuid4
    assert loader.load("c932f581-6430-4ae1-ad63-85489a0206b2", uuid.UUID) == uuid.UUID(
        "c932f581-6430-4ae1-ad63-85489a0206b2"
    )
    # uuid6
    assert loader.load("1f0d1144-17c1-6152-a18b-98af65b3c73e", uuid.UUID) == uuid.UUID(
        "1f0d1144-17c1-6152-a18b-98af65b3c73e"
    )
    # uuid7
    assert loader.load("019ae987-1dc6-770d-88c2-ec9b62f79444", uuid.UUID) == uuid.UUID(
        "019ae987-1dc6-770d-88c2-ec9b62f79444"
    )


def test_load_literal() -> None:
    from typing import Literal

    loader = Loader()

    Foo = Literal[1, 2, 3, "foo"]
    assert loader.load(2, Foo) == 2
    assert loader.load("foo", Foo) == "foo"
    with pytest.raises(TressedValueError) as exc_info:
        loader.load(5, Foo)
    assert str(exc_info.value) == (
        "Failed to load value of type int at path . into type form Literal[1, 2, 3, 'foo']: "
        "got value 5 but expected one of: 1, 2, 3, 'foo'"
    )


def test_load_type_alias() -> None:
    from typing import Literal

    loader = Loader()

    type TruthyLiteral = Literal[True, "true", "t", "yes", "y", "1"]
    type IntPair = tuple[int, int]
    assert loader.load("yes", TruthyLiteral) == "yes"
    assert loader.load([1, 2], IntPair) == (1, 2)


def test_load_generic_type_alias() -> None:
    loader = Loader()

    type Pair[T] = tuple[T, T]
    type IntPair = Pair[int]
    type StrPair = Pair[str]

    assert loader.load((1, 0), IntPair) == (1, 0)
    assert loader.load(("yes", "no"), StrPair) == ("yes", "no")

    with pytest.raises(TressedValueError) as exc_info:
        loader.load((1, 0), Pair) == (1, 0)
    assert str(exc_info.value) == (
        "Failed to load value of type tuple at path . into type form Pair[T=?]: "
        "type form should have only concrete type parameters"
    )

    type SomeMapping[K, V] = dict[K, V]
    type IntMapping[K] = dict[K, int]

    assert loader.load({"foo": 1}, IntMapping[str]) == {"foo": 1}

    with pytest.raises(TressedValueError) as exc_info:
        loader.load({"foo": 1}, IntMapping)
    assert str(exc_info.value) == (
        "Failed to load value of type dict at path . into type form IntMapping[K=?]: "
        "type form should have only concrete type parameters"
    )

    with pytest.raises(TressedValueError) as exc_info:
        loader.load({"foo": 1}, SomeMapping[int])  # type: ignore[arg-type]
    assert str(exc_info.value) == (
        "Failed to load value of type dict at path . into type form SomeMapping[K=int, V=?]: "
        "type form should have only concrete type parameters"
    )


def test_load_optional() -> None:
    loader = Loader()

    # T | None
    assert loader.load(1, int | None) == 1
    assert loader.load(1, None | int) == 1
    assert loader.load(None, int | None) is None
    assert loader.load(None, None | int) is None
    with pytest.raises(TressedValueError):
        assert loader.load("foo", int | None)


def test_load_legacy_optional() -> None:
    from typing import Optional, Union

    loader = Loader()

    # typing.Optional[T]
    assert loader.load(1, Optional[int]) == 1
    assert loader.load(None, Optional[int]) is None
    assert loader.load(None, Optional[None]) is None
    with pytest.raises(TressedValueError):
        assert loader.load("foo", Optional[int])

    # typing.Union[T, None], typing.Union[None, T]
    assert loader.load(1, Union[int, None]) == 1
    assert loader.load(None, Union[int, None]) is None
    assert loader.load(1, Union[None, int]) == 1
    assert loader.load(None, Union[None, int]) is None
    assert loader.load(None, Union[None, None]) is None
    with pytest.raises(TressedValueError):
        assert loader.load("foo", Union[int, None])


def test_load_union() -> None:
    loader = Loader()

    assert loader.load(1, int | str) == 1
    assert loader.load("foo", int | str) == "foo"

    with pytest.raises(TressedValueError) as exc_info:
        loader.load([1, 2], int | str)
    assert (
        str(exc_info.value)
        == "Failed to load value of type list at path . into type form int | str (2 sub-exceptions)"
    )
    assert [str(e) for e in exc_info.value.exceptions] == [
        "Failed to load value of type list at path . into type form int",
        "Failed to load value of type list at path . into type form str",
    ]


def test_load_legacy_union() -> None:
    from typing import Union

    loader = Loader()

    assert loader.load(1, Union[int, str]) == 1
    assert loader.load("foo", Union[int, str]) == "foo"

    with pytest.raises(TressedValueError) as exc_info:
        loader.load([1, 2], Union[int, str])
    assert (
        str(exc_info.value)
        == "Failed to load value of type list at path . into type form int | str (2 sub-exceptions)"
    )
    assert [str(e) for e in exc_info.value.exceptions] == [
        "Failed to load value of type list at path . into type form int",
        "Failed to load value of type list at path . into type form str",
    ]


def test_load_path() -> None:
    from pathlib import Path, PurePosixPath, PureWindowsPath

    loader = Loader()

    assert loader.load("/foo/bar/baz", Path) == Path("/foo/bar/baz")
    assert loader.load("/foo/bar/baz", PurePosixPath) == PurePosixPath("/foo/bar/baz")
    assert loader.load("/foo/bar/baz", PureWindowsPath) == PureWindowsPath(
        "/foo/bar/baz"
    )


def test_load_datetime() -> None:
    from datetime import UTC, date, datetime, time, timedelta, timezone

    loader = Loader()
    assert loader.load("12:45:59", time) == time(12, 45, 59)
    assert loader.load("12:45:59Z", time) == time(12, 45, 59, tzinfo=UTC)
    assert loader.load("12:45:59-00:30", time) == time(
        12, 45, 59, tzinfo=timezone(timedelta(seconds=-1800))
    )
    assert loader.load("2025-12-29", date) == date(2025, 12, 29)
    assert loader.load("2025-12-29T12:45:59", datetime) == datetime(
        2025, 12, 29, 12, 45, 59
    )
    assert loader.load("2025-12-29T12:45:59Z", datetime) == datetime(
        2025, 12, 29, 12, 45, 59, tzinfo=UTC
    )
    assert loader.load("2025-12-29T12:45:59+02:00", datetime) == datetime(
        2025, 12, 29, 12, 45, 59, tzinfo=timezone(timedelta(seconds=7200))
    )


def test_load_discriminated_union_first_match() -> None:
    from typing import Annotated, Literal, NamedTuple, get_args, get_type_hints

    from tressed.discriminated_union import Discriminator

    class Foo(NamedTuple):
        tag: Literal["foo"]
        field1: str
        field2: int
        field4: tuple[int, int] = (6, 6)

    class Bar(NamedTuple):
        tag: Literal["bar", "BAR"]
        field2: int
        field3: float
        field5: tuple[int, int] = (6, 7)

    loader = Loader()

    def _match_tag(value: Any, type_form: TypeForm) -> bool:
        tags = get_args(get_type_hints(type_form)["tag"])
        return value["tag"] in tags

    type TaggedUnion = Annotated[Foo | Bar, Discriminator(_match_tag)]

    assert loader.load(
        {"tag": "foo", "field1": "hej", "field2": 123}, TaggedUnion
    ) == Foo(tag="foo", field1="hej", field2=123, field4=(6, 6))
    assert loader.load(
        {"tag": "bar", "field2": 123, "field3": 1.23}, TaggedUnion
    ) == Bar(tag="bar", field2=123, field3=1.23, field5=(6, 7))
    assert loader.load(
        {"tag": "BAR", "field2": 123, "field3": 1.23}, TaggedUnion
    ) == Bar(tag="BAR", field2=123, field3=1.23, field5=(6, 7))
    with pytest.raises(TressedValueError) as exc_info:
        loader.load({"tag": "baz", "field2": 123, "field3": 1.23}, TaggedUnion)
    assert str(exc_info.value) == (
        "Failed to load value of type dict at path . into type form Annotated[Foo | Bar]: "
        "value did not match discriminated union discriminant"
    )


def test_load_discriminated_union_best_match() -> None:
    from typing import Annotated, NamedTuple

    from tressed.discriminated_union import Discriminator

    class Foo(NamedTuple):
        field1: str
        field2: int
        field4: tuple[int, int] = (6, 6)

    class Bar(NamedTuple):
        field2: int
        field3: float
        field5: tuple[int, int] = (6, 7)

    loader = Loader()

    def _match_num_fields(value: Any, type_form: TypeForm) -> int:
        print(f"{value=} {type_form=} {set(type_form._fields) & set(value.keys())=}")
        return len(set(type_form._fields) & set(value.keys()))

    type BestUnion = Annotated[
        Foo | Bar, Discriminator(_match_num_fields, strategy="best-match")
    ]

    assert loader.load({"field1": "foo", "field2": 123}, BestUnion) == Foo(
        field1="foo", field2=123, field4=(6, 6)
    )
    assert loader.load({"field2": 123, "field3": 6.7}, BestUnion) == Bar(
        field2=123, field3=6.7, field5=(6, 7)
    )

    with pytest.raises(TressedValueError) as exc_info:
        loader.load({"foo": "bar"}, BestUnion)
    assert str(exc_info.value) == (
        "Failed to load value of type dict at path . into type form Annotated[Foo | Bar]: "
        "value did not match discriminated union discriminant"
    )

    # ambiguous
    with pytest.raises(TressedValueError) as exc_info:
        loader.load({"field2": "bar"}, BestUnion)
    assert str(exc_info.value) == (
        "Failed to load value of type dict at path . into type form Annotated[Foo | Bar]: "
        "value did not match discriminated union discriminant"
    )
