from gluetypes.exceptions import GluetypesValueError

TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import Any
    from gluetypes.loader.types import TypePath, LoaderProtocol

__all__ = [
    "load_simple_scalar",
    "load_simple_sequence",
    "load_tuple",
]


def load_simple_scalar[T](
    value: Any, type_form: type[T], type_path: TypePath, loader: LoaderProtocol
) -> T:
    if type(value) is type_form:
        return value
    raise GluetypesValueError(
        f"Cannot to load value {value!r} at path {type_path!r} into {type_form.__name___}"
    )


def load_simple_sequence[T](
    value: Any, type_form: type[T], type_path: TypePath, loader: LoaderProtocol
) -> T:
    from gluetypes.predicates import get_origin, get_args

    origin = get_origin(type_form)
    num_expected_args = 2 if origin is tuple else 1
    args = get_args(type_form)
    if origin is None or args is None or len(args) != num_expected_args:
        raise GluetypesValueError(
            f"Cannot to load value {value!r} at path {type_path!r}, "
            f"{getattr(type_form, '__name__', type_form)} is not a homogeneous generic type"
        )

    item_type = args[0]
    return origin(
        loader._load(item, item_type, (*type_path, pos))
        for pos, item in enumerate(value)
    )


def load_tuple[*Ts](
    value: Any, type_form: tuple[*Ts], type_path: TypePath, loader: LoaderProtocol
) -> tuple[*Ts]:
    from gluetypes.predicates import get_origin, get_args

    origin = get_origin(type_form)
    args = get_args(type_form)
    if origin is None or args is None:
        raise GluetypesValueError(
            f"Cannot to load value {value!r} at path {type_path!r}, "
            f"{getattr(type_form, '__name__', type_form)} is not a generic type"
        )

    return tuple(
        loader._load(item, args[pos], (*type_path, pos))
        for pos, item in enumerate(value)
    )
