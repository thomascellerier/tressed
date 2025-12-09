import sys

TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import Any

    from tressed.dumper.types import Dumped, DumperProtocol
    from tressed.exceptions import TressedValueError
    from tressed.type_path import TypePath

__all__ = [
    "dump_identity",
    "dump_simple_sequence",
    "dump_simple_mapping",
    "dump_simple_scalar",
    "dump_complex",
    "dump_enum",
    "dump_datetime",
    "dump_dataclass",
]


def dump_identity(value: Any, type_path: TypePath, dumper: DumperProtocol) -> Dumped:
    return value


def dump_simple_scalar(
    value: Any, type_path: TypePath, dumper: DumperProtocol
) -> Dumped:
    return str(value)


def dump_simple_sequence(
    value: Any, type_path: TypePath, dumper: DumperProtocol
) -> Dumped:
    return [dumper._dump(item, (*type_path, i)) for i, item in enumerate(value)]


def dump_complex(value: Any, type_path: TypePath, dumper: DumperProtocol) -> Dumped:
    return [value.real, value.imag]


def _dump_key(key: Any, type_path: TypePath, dumper: DumperProtocol) -> str:
    key_path = (*type_path, key)
    dumped_key = dumper._dump(key, key_path)
    if type(dumped_key) is not str:
        raise TressedValueError(key, type(key), key_path, "dumped key must be a string")
    return dumped_key


def dump_simple_mapping(
    value: Any, type_path: TypePath, dumper: DumperProtocol
) -> Dumped:
    return {
        _dump_key(item_key, type_path, dumper): dumper._dump(
            item_value, (*type_path, item_key)
        )
        for item_key, item_value in value.items()
    }


def dump_enum(value: Any, type_path: TypePath, dumper: DumperProtocol) -> Dumped:
    return dumper._dump(value.value, type_path)


def dump_datetime(value: Any, type_path: TypePath, dumper: DumperProtocol) -> Dumped:
    dumped = value.isoformat()
    # Return datetime.{date,datetime,time}.isoformat() with the one difference that we use
    # a Z suffix instead of +00:00 to keep the output more compact and more like the usual datetimes
    # seen in json payloads.
    zero_suffix = "+00:00"
    if dumped.endswith(zero_suffix):
        return dumped[: -len(zero_suffix)] + "Z"
    return dumped


def dump_dataclass(value: Any, type_path: TypePath, dumper: DumperProtocol) -> Dumped:
    from dataclasses import MISSING, fields

    dumped = {}
    for field in fields(value):
        if not field.repr or not field.init:
            continue

        name = field.name

        field_value = getattr(value, name)

        if dumper.hide_defaults:
            if (default_value := field.default) is not MISSING:
                if field_value == default_value:
                    continue

            elif (default_factory := field.default_factory) is not MISSING:
                # Avoid calling the default factory function if its a known mutable type like list
                if default_factory in frozenset({list, set, dict}) and len(value) == 0:
                    continue

                # Avoid calling default factory if we know the value can't match the default
                cant_be_default = (
                    uuid := sys.modules.get("uuid")
                ) and default_factory in frozenset(
                    {
                        uuid.uuid1,
                        uuid.uuid4,
                        uuid.uuid6,
                        uuid.uuid7,
                    }
                )
                if not cant_be_default and field_value == default_factory():
                    continue

        alias = dumper._resolve_alias(type(value), type_path, name)
        dumped[alias] = dumper._dump(field_value, (*type_path, alias))

    return dumped
