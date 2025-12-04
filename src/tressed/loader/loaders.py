import sys

from tressed.exceptions import TressedValueError

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any

    from typing_extensions import TypeForm

    from tressed.loader.types import LoaderProtocol, TypePath

# TODO:
# - typing.Optional[T]
# - T1 | .. | T2, typing.Union[T]
# - pathlib.Path
# - datatime.datetime
# - datetime.date
# - datetime.time
# - uuid.UUID
# - enum.Enum
# - Tagged union using Annotated

__all__ = [
    "load_identity",
    "load_simple_scalar",
    "load_simple_collection",
    "load_tuple",
    "load_dataclass",
    "load_newtype",
    "load_typeddict",
    "load_namedtuple",
]

if TYPE_CHECKING:
    from enum import Enum, auto

    class _MissingType(Enum):
        _MISSING = auto()

    _MISSING = _MissingType._MISSING

else:
    _MISSING = object()


def _type_path_repr(type_path: TypePath) -> str:
    return f".{'.'.join(map(str, type_path))}"


def _type_form_repr(type_form: TypeForm) -> str:
    if name := getattr(type_form, "__name__", None):
        return name
    return repr(type_form)


def _items(value: Any) -> Iterator[tuple[Any, Any]]:
    type_ = type(value)
    if type_ is dict:
        return value.items()
    elif (argparse := sys.modules.get("argparse")) and type_ is argparse.Namespace:
        return vars(value).items()
    else:
        return value.items()


def load_identity[T](
    value: Any, type_form: TypeForm[T], type_path: TypePath, loader: LoaderProtocol
) -> T:
    """
    Pass the value as is, given that it is of the expected type.
    """
    if type(value) is type_form:
        return value
    raise TressedValueError(
        f"Cannot to load value {value!r} at path {_type_path_repr(type_path)} into {_type_form_repr(type_form)}"
    )


def load_simple_scalar[T](
    value: Any, type_form: TypeForm[T], type_path: TypePath, loader: LoaderProtocol
) -> T:
    """
    Construct an instance of the given type using the value as the sole argument.
    """
    return type_form(value)  # type: ignore[call-arg]


def load_float[T](
    value: Any, type_form: TypeForm[T], type_path: TypePath, loader: LoaderProtocol
) -> T:
    """
    Load float with int promotion.
    """
    type_ = type(value)
    if type_ is float:
        return value
    if type_ is int:
        return type_form(value)  # type: ignore[call-arg]
    raise TressedValueError(
        f"Cannot to load value {value!r} at path {_type_path_repr(type_path)} into {_type_form_repr(type_form)}"
    )


def load_complex[T](
    value: Any, type_form: TypeForm[T], type_path: TypePath, loader: LoaderProtocol
) -> T:
    """
    Load complex from a sequence a pair of floats.
    """
    real = loader._load(value[0], float, (*type_path, 0))
    imag = loader._load(value[1], float, (*type_path, 1))
    return type_form(real, imag)  # type: ignore[call-arg]


def load_dict[T](
    value: Any, type_form: TypeForm[T], type_path: TypePath, loader: LoaderProtocol
) -> T:
    from tressed.predicates import get_args

    args = get_args(type_form)

    assert args is not None
    assert len(args) == 2

    key_type, value_type = args
    return {  # type: ignore[return-value]
        loader._load(
            item_key, key_type, (item_path := (*type_path, item_key))
        ): loader._load(item_value, value_type, item_path)
        for item_key, item_value in _items(value)
    }


def load_simple_collection[T](
    value: Any, type_form: TypeForm[T], type_path: TypePath, loader: LoaderProtocol
) -> T:
    from tressed.predicates import get_args, get_origin

    origin = get_origin(type_form)
    num_expected_args = 2 if origin is tuple else 1
    args = get_args(type_form)
    if origin is None or args is None or len(args) != num_expected_args:
        raise TressedValueError(
            f"Cannot to load value {value!r} at path {_type_path_repr(type_path)}, "
            f"{_type_form_repr(type_form)} is not a homogeneous generic type"
        )

    item_type = args[0]
    return origin(
        loader._load(item, item_type, (*type_path, pos))
        for pos, item in enumerate(value)
    )


def load_tuple[T](
    value: Any, type_form: TypeForm[T], type_path: TypePath, loader: LoaderProtocol
) -> T:
    from tressed.predicates import get_args, get_origin

    origin = get_origin(type_form)
    args = get_args(type_form)
    if origin is None or args is None:
        raise TressedValueError(
            f"Cannot to load value {value!r} at path {_type_path_repr(type_path)}, "
            f"{getattr(type_form, '__name__', type_form)} is not a generic type"
        )

    return tuple(  # type: ignore[return-value]
        loader._load(item, args[pos], (*type_path, pos))
        for pos, item in enumerate(value)
    )


def load_dataclass[T](
    value: Any, type_form: TypeForm[T], type_path: TypePath, loader: LoaderProtocol
) -> T:
    from dataclasses import fields

    loaded = {}

    for field in fields(type_form):  # type: ignore[arg-type]
        field_name = field.name
        alias = loader._resolve_alias(type_form, type_path, field_name)
        if not field.init:
            continue
        if (field_value := value.get(alias, _MISSING)) is not _MISSING:
            loaded[field_name] = field_value
    return type_form(**loaded)


def load_newtype[T: TypeForm](
    value: Any, type_form: T, type_path: TypePath, loader: LoaderProtocol
) -> T:
    supertype = getattr(type_form, "__supertype__")
    return loader._load(value, supertype, type_path)


def _is_extra_items_sentinel(value: Any) -> bool:
    if (typing := sys.modules.get("typing")) and hasattr(typing, "NoExtraItems"):
        if value is getattr(typing, "NoExtraItems"):
            return True
    if typing_extensions := sys.modules.get("typing_extensions"):
        if value is typing_extensions.NoExtraItems:
            return True
    return False


def load_typeddict[T](
    value: Any, type_form: TypeForm[T], type_path: TypePath, loader: LoaderProtocol
) -> T:
    values: dict[str, Any] = {}
    required_keys = getattr(type_form, "__required_keys__")
    optional_keys = getattr(type_form, "__optional_keys__")
    valid_keys = required_keys | optional_keys

    closed = getattr(type_form, "__closed__", None)
    extra_items = getattr(type_form, "__extra_items__", _MISSING)
    if _is_extra_items_sentinel(extra_items):
        extra_items = _MISSING

    extra_keys: set[str] | None = None
    for item_key, item_value in _items(value):
        if extra_items is not _MISSING:
            if item_key not in valid_keys:
                values[item_key] = loader._load(
                    item_value, extra_items, (*type_path, item_key)
                )
                continue

        elif closed:
            if item_key not in valid_keys:
                if extra_keys is None:
                    extra_keys = set()
                extra_keys.add(item_key)
                continue

        values[item_key] = item_value

    if missing_keys := (required_keys - values.keys()):
        raise TressedValueError(
            f"Failed to load value of type {_type_form_repr(type(value))} into {_type_form_repr(type_form)} "
            f"at path {_type_path_repr(type_path)}, "
            f"missing required keys {', '.join(map(repr, missing_keys))}: {value}"
        )

    if extra_keys:
        raise TressedValueError(
            f"Failed to load value of type {_type_form_repr(type(value))} into {_type_form_repr(type_form)} "
            f"at path {_type_path_repr(type_path)}, "
            f"extra keys {', '.join(sorted(map(repr, extra_keys)))}: {value}"
        )

    return values  # type: ignore[return-value]


def load_namedtuple[T](
    value: Any, type_form: TypeForm[T], type_path: TypePath, loader: LoaderProtocol
) -> T:
    from typing import get_type_hints

    type_hints = get_type_hints(type_form)
    values: dict[str, Any] = {
        key: loader._load(field_value, type_hints[key], (*type_path, key))
        for key, field_value in _items(value)
    }
    return type_form(**values)
