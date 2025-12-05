import sys

from tressed.exceptions import TressedValueError
from tressed.predicates import get_args, get_origin, is_union_type
from tressed.type_form import type_form_repr

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any

    from typing_extensions import TypeForm

    from tressed.loader.types import LoaderProtocol, TypePath

__all__ = [
    "load_identity",
    "load_simple_scalar",
    "load_float",
    "load_complex",
    "load_dict",
    "load_simple_collection",
    "load_tuple",
    "load_dataclass",
    "load_newtype",
    "load_typeddict",
    "load_namedtuple",
    "load_literal",
    "load_type_alias",
    "load_optional",
    "load_union",
    "load_datetime",
    "load_discriminated_union",
]

if TYPE_CHECKING:
    from enum import Enum, auto

    class _MissingType(Enum):
        _MISSING = auto()

    _MISSING = _MissingType._MISSING

else:
    _MISSING = object()


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
        value,
        type_form,
        type_path,
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
        value,
        type_form,
        type_path,
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
    origin = get_origin(type_form)
    num_expected_args = 2 if origin is tuple else 1
    args = get_args(type_form)
    if origin is None or args is None or len(args) != num_expected_args:
        raise TressedValueError(
            value,
            type_form,
            type_path,
            f"{type_form_repr(type_form)} is not a homogeneous generic type",
        )

    item_type = args[0]
    return origin(
        loader._load(item, item_type, (*type_path, pos))
        for pos, item in enumerate(value)
    )


def load_tuple[T](
    value: Any, type_form: TypeForm[T], type_path: TypePath, loader: LoaderProtocol
) -> T:
    origin = get_origin(type_form)
    args = get_args(type_form)
    if origin is None or args is None:
        raise TressedValueError(
            value,
            type_form,
            type_path,
            f"{getattr(type_form, '__name__', type_form)} is not a generic type",
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
            value,
            type_form,
            type_path,
            f"missing required keys {', '.join(map(repr, missing_keys))}: {value}",
        )

    if extra_keys:
        raise TressedValueError(
            value,
            type_form,
            type_path,
            f"extra keys {', '.join(sorted(map(repr, extra_keys)))}: {value}",
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


def load_literal[T](
    value: Any, type_form: TypeForm[T], type_path: TypePath, loader: LoaderProtocol
) -> T:
    args = get_args(type_form)
    assert args is not None
    if value in args:
        return value
    raise TressedValueError(
        value,
        type_form,
        type_path,
        f"got value {repr(value)} but expected one of: {', '.join(map(repr, args))}",
    )


def load_type_alias[T](
    value: Any, type_form: TypeForm[T], type_path: TypePath, loader: LoaderProtocol
) -> T:
    evaluated_type = type_form.evaluate_value()  # type: ignore[attr-defined]
    if (num_params := len(type_form.__type_params__)) > 0:
        args = get_args(type_form)
        if args is None or len(args) < num_params:
            raise TressedValueError(
                value,
                type_form,
                type_path,
                "type form should have only concrete type parameters",
            )

        evaluated_type = evaluated_type[*args]

    return loader._load(value, evaluated_type, type_path)


def load_optional[T](
    value: Any, type_form: TypeForm[T], type_path: TypePath, loader: LoaderProtocol
) -> T:
    if value is None:
        return value  # type: ignore[return-value]

    args = get_args(type_form)
    match args:
        case [T, NoneType] if NoneType is type(None):
            return loader._load(value, T, type_path)
        case [NoneType, T] if NoneType is type(None):
            return loader._load(value, T, type_path)
        case [T]:
            return loader._load(value, T, type_path)
        case _:
            assert False, "unreachable"


def load_union[T](
    value: Any, type_form: TypeForm[T], type_path: TypePath, loader: LoaderProtocol
) -> T:
    args = get_args(type_form)
    assert args, "unreachable"

    errors = None
    for arg in args:
        try:
            return loader._load(value, arg, type_path)
        except TressedValueError as error:
            if errors is None:
                errors = []
            errors.append(error)

    assert args, "unreachable"
    raise TressedValueError(
        value,
        type_form,
        type_path,
        exceptions=errors,
    )


def load_datetime[T](
    value: Any, type_form: TypeForm[T], type_path: TypePath, loader: LoaderProtocol
) -> T:
    return type_form.fromisoformat(value)  # type: ignore[attr-defined]


def load_discriminated_union[T](
    value: Any, type_form: TypeForm[T], type_path: TypePath, loader: LoaderProtocol
) -> T:
    from tressed.discriminated_union import Discriminator

    args = get_args(type_form)
    assert args is not None, "unreachable"

    union_type = next(arg for arg in args if is_union_type(arg))
    union_args = get_args(union_type)
    assert union_args

    discriminator = next(
        metadata
        for metadata in type_form.__metadata__  # type: ignore[attr-defined]
        if isinstance(metadata, Discriminator)
    )

    matched_type_form = discriminator.match(value, *union_args)
    if matched_type_form is None:
        raise TressedValueError(
            value,
            type_form,
            type_path,
            "value did not match discriminated union discriminant",
        )
    return loader._load(value, matched_type_form, type_path)
