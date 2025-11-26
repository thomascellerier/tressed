# TODO: Use python3.15+ lazy imports instead
# TODO: Switch to TypeForm https://peps.python.org/pep-0747/ once available
from __future__ import annotations

from gluetypes.exceptions import GluetypesTypeError, GluetypesValueError

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from typing import Any, Protocol

    type TypePath = tuple[str | int, ...]

    class LoaderProtocol(Protocol):
        def _load[T](
            self, value: Any, type_form: type[T], type_path: TypePath
        ) -> T: ...

    type TypeLoaderFn[T] = Callable[[Any, type[T], TypePath, LoaderProtocol], T]


__all__ = [
    "Loader",
]


def _load_simple_type[T](
    value: Any, type_form: type[T], type_path: TypePath, loader: LoaderProtocol
) -> T:
    if type(value) is type_form:
        return value
    raise GluetypesValueError(
        f"Cannot to load value {value!r} at path {type_path!r} into {type_form.__name___}"
    )


NoneType = type(None)


_simple_type_loaders = {
    bool: _load_simple_type,
    int: _load_simple_type,
    float: _load_simple_type,
    str: _load_simple_type,
    NoneType: _load_simple_type,
}
_default_type_loaders = _simple_type_loaders


class Loader:
    def __init__(
        self, type_loaders: Mapping[type, TypeLoaderFn] = _default_type_loaders
    ) -> None:
        self._type_loaders: Mapping[type, TypeLoaderFn] = type_loaders

    def _load[T](self, value: Any, type_form: type[T], type_path: TypePath) -> T:
        if type_loader := self._type_loaders.get(type_form):
            try:
                return type_loader(value, type_form, type_path, self)
            except GluetypesValueError:
                raise
            except Exception as e:
                raise GluetypesValueError(
                    f"Failed to load value {value!r} at path {type_path!r} into type form {type_form!r}"
                ) from e
        raise GluetypesTypeError(
            f"Unhandled type form {type_form!r} at path {type_path!r} for value {value!r}"
        )

    def load[T](self, value: Any, type_form: type[T]) -> T:
        return self._load(value, type_form, ())
