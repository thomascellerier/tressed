from tressed.exceptions import TressedValueError

TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import Any

    from typing_extensions import TypeForm

    from tressed.loader.types import LoaderProtocol, TypePath

__all__ = [
    "load_simple_scalar",
    "load_simple_collection",
    "load_tuple",
    "load_dataclass",
    "load_newtype",
]


def load_simple_scalar[T](
    value: Any, type_form: TypeForm[T], type_path: TypePath, loader: LoaderProtocol
) -> T:
    if type(value) is type_form:
        return value
    if (name := getattr(type_form, "__name__", None)) is None:
        name = repr(type_form)
    raise TressedValueError(
        f"Cannot to load value {value!r} at path {type_path!r} into {name}"
    )


def load_simple_collection[T](
    value: Any, type_form: TypeForm[T], type_path: TypePath, loader: LoaderProtocol
) -> T:
    from tressed.predicates import get_args, get_origin

    origin = get_origin(type_form)
    num_expected_args = 2 if origin is tuple else 1
    args = get_args(type_form)
    if origin is None or args is None or len(args) != num_expected_args:
        raise TressedValueError(
            f"Cannot to load value {value!r} at path {type_path!r}, "
            f"{getattr(type_form, '__name__', type_form)} is not a homogeneous generic type"
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
            f"Cannot to load value {value!r} at path {type_path!r}, "
            f"{getattr(type_form, '__name__', type_form)} is not a generic type"
        )

    return tuple(  # type: ignore[return-value]
        loader._load(item, args[pos], (*type_path, pos))
        for pos, item in enumerate(value)
    )


def load_dataclass[T](
    value: Any, type_form: TypeForm[T], type_path: TypePath, loader: LoaderProtocol
) -> T:
    from dataclasses import MISSING, fields

    loaded = {}

    for field in fields(type_form):  # type: ignore[arg-type]
        field_name = field.name
        alias = loader._resolve_alias(type_form, type_path, field_name)
        if (field_value := value.get(alias, MISSING)) is not MISSING:
            loaded[field_name] = field_value

    return type_form(**loaded)


def load_newtype[T: TypeForm](
    value: Any, type_form: T, type_path: TypePath, loader: LoaderProtocol
) -> T:
    supertype = getattr(type_form, "__supertype__")
    return loader._load(value, supertype, type_path)
