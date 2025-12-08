from tressed.dumper import Dumper


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
