import pytest

from tressed.dumper import Dumper
from tressed.exceptions import TressedTypeError


def test_dump_basic_types() -> None:
    dumper = Dumper()

    assert dumper.dump(1) == 1
    assert dumper.dump(1.23) == 1.23
    assert dumper.dump("foo") == "foo"
    assert dumper.dump(True) is True
    assert dumper.dump(False) is False
    assert dumper.dump(None) is None


def test_dump_simple_sequence() -> None:
    dumper = Dumper()

    assert dumper.dump([1, 2, 3]) == [1, 2, 3]
    assert dumper.dump((1, 2, 3)) == [1, 2, 3]

    dumped = dumper.dump({1, 2, 3})
    assert isinstance(dumped, list)
    assert sorted(dumped) == [1, 2, 3]  # type: ignore[type-var]

    dumped = dumper.dump(frozenset({1, 2, 3}))
    assert isinstance(dumped, list)
    assert sorted(dumped) == [1, 2, 3]  # type: ignore[type-var]


def test_dump_ipaddress() -> None:
    import ipaddress

    dumper = Dumper()

    assert dumper.dump(ipaddress.IPv4Address("127.0.0.1")) == "127.0.0.1"
    assert dumper.dump(ipaddress.IPv6Address("::1")) == "::1"

    assert dumper.dump(ipaddress.IPv4Network("127.0.0.0/24")) == "127.0.0.0/24"
    assert dumper.dump(ipaddress.IPv6Network("::0/64")) == "::/64"

    assert dumper.dump(ipaddress.IPv4Interface("127.0.0.1/24")) == "127.0.0.1/24"
    assert dumper.dump(ipaddress.IPv6Interface("::1/64")) == "::1/64"


def test_dump_enum() -> None:
    import enum

    class SampleEnum(enum.Enum):
        FOO = (1, 2)

    class SampleStrEnum(enum.StrEnum):
        BAR = enum.auto()

    class SampleIntEnum(enum.IntEnum):
        BAZ = enum.auto()

    dumper = Dumper()

    assert dumper.dump(SampleEnum.FOO) == [1, 2]
    assert dumper.dump(SampleStrEnum.BAR) == "bar"
    assert dumper.dump(SampleIntEnum.BAZ) == 1


def test_dump_datetime() -> None:
    from datetime import UTC, date, datetime, time, timedelta, timezone

    dumper = Dumper()
    assert dumper.dump(time(12, 45, 59)) == "12:45:59"
    assert dumper.dump(time(12, 45, 59, tzinfo=UTC)) == "12:45:59Z"
    assert (
        dumper.dump(time(12, 45, 59, tzinfo=timezone(timedelta(seconds=-1800))))
        == "12:45:59-00:30"
    )
    assert dumper.dump(date(2025, 12, 29)) == "2025-12-29"
    assert dumper.dump(datetime(2025, 12, 29, 12, 45, 59)) == "2025-12-29T12:45:59"
    assert (
        dumper.dump(datetime(2025, 12, 29, 12, 45, 59, tzinfo=UTC))
        == "2025-12-29T12:45:59Z"
    )
    assert (
        dumper.dump(
            datetime(2025, 12, 29, 12, 45, 59, tzinfo=timezone(timedelta(seconds=7200)))
        )
        == "2025-12-29T12:45:59+02:00"
    )


def test_dump_dataclass() -> None:
    import uuid
    from dataclasses import dataclass, field

    from tressed.alias import to_pascal

    @dataclass
    class SomeDataclass:
        foo: str
        some_secret: str = field(repr=False)
        bar: str = "bar"
        baz: list[int] = field(default_factory=lambda: [1, 2, 3])
        bar_bar: tuple[int, str] = field(metadata={"alias": "barBar"}, kw_only=True)
        some_id: uuid.UUID = field(default_factory=uuid.uuid4)
        some_lazy_field: int = field(init=False)

        def __post_init__(self) -> None:
            self.some_lazy_field = len(self.baz)

    value = SomeDataclass(
        foo="FOO",
        some_secret="hehe",
        bar="bar",
        bar_bar=(123, "Hej ho!"),
        some_id=uuid.UUID("c932f581-6430-4ae1-ad63-85489a0206b2"),
    )
    assert value.some_lazy_field == 3

    dumper = Dumper(alias_fn=to_pascal)
    assert dumper.dump(value) == {
        "Bar": "bar",
        "Baz": [1, 2, 3],
        "Foo": "FOO",
        "barBar": [123, "Hej ho!"],
        "SomeId": "c932f581-6430-4ae1-ad63-85489a0206b2",
    }

    dumper_hide_defaults = Dumper(alias_fn=to_pascal, hide_defaults=True)
    assert dumper_hide_defaults.dump(value) == {
        "Foo": "FOO",
        "barBar": [123, "Hej ho!"],
        "SomeId": "c932f581-6430-4ae1-ad63-85489a0206b2",
    }


def test_dump_namedtuple() -> None:
    from typing import NamedTuple

    from tressed.alias import to_camel

    class SomeNamedTuple(NamedTuple):
        some_field: int
        some_default_field: str = "foobar"

    value = SomeNamedTuple(some_field=123)

    dumper = Dumper(alias_fn=to_camel)
    assert dumper.dump(value) == {"someField": 123, "someDefaultField": "foobar"}

    dumper = Dumper(hide_defaults=True)
    assert dumper.dump(value) == {"some_field": 123}


def test_dump_unknown_type() -> None:
    class UnknownType:
        def __repr__(self) -> str:
            return f"{self.__class__.__name__}()"

    dumper = Dumper()

    with pytest.raises(TressedTypeError) as exc_info:
        dumper.dump(UnknownType())
    assert (
        str(exc_info.value)
        == "Unhandled type UnknownType at path . for value UnknownType()"
    )


def test_dump_custom_type() -> None:
    from typing import Any

    from tressed import TypeForm, TypePath
    from tressed.dumper import Dumped, DumperProtocol

    class CustomType:
        def __init__(self, value: int) -> None:
            self.value = value

    def _is_custom_type(type_form: TypeForm) -> bool:
        if type(type_form) is type:
            return issubclass(type_form, CustomType)
        else:
            return False

    def _dump_custom_type(
        value: Any, type_path: TypePath, dumper: DumperProtocol
    ) -> Dumped:
        return [f"Custom value is {value.value}", value.value]

    dumper = Dumper(extra_type_handlers={CustomType: _dump_custom_type})
    assert dumper.dump(CustomType(123)) == ["Custom value is 123", 123]

    dumper = Dumper(extra_type_mappers={_is_custom_type: _dump_custom_type})
    assert dumper.dump(CustomType(123)) == ["Custom value is 123", 123]


def test_barebones_dumper() -> None:
    dumper = Dumper(
        default_type_handlers={int: lambda v, _, __: "*" * v},
        default_type_mappers={lambda t: t is tuple: lambda v, _, __: len(v)},
    )
    assert dumper.dump(10) == "**********"
    assert dumper.dump(("oo", "bar", "baz")) == 3

    with pytest.raises(TressedTypeError) as exc_info:
        dumper.dump(10.6) == "Unhandled type float at path . for value 10.6"

    with pytest.raises(TressedTypeError) as exc_info:
        dumper.dump("foo")
    assert str(exc_info.value) == "Unhandled type str at path . for value 'foo'"


def test_dump_path() -> None:
    from pathlib import Path

    dumper = Dumper()
    assert dumper.dump(Path("/foo/bar")) == "/foo/bar"

    class CustomPath:
        def __init__(self, value: int) -> None:
            self.value = value

        def __fspath__(self) -> str:
            return "/".join(["foo"] * self.value)

    assert dumper.dump(CustomPath(3)) == "foo/foo/foo"
