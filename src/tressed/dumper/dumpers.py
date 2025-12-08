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
    "dump_enum",
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
