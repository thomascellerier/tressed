# TODO: Use python3.15+ lazy imports instead
# TODO: Switch to TypeForm https://peps.python.org/pep-0747/ once available
from __future__ import annotations

from gluetypes.exceptions import GluetypesTypeError, GluetypesValueError
from gluetypes.predicates import (
    is_tuple,
    is_list,
    is_homogeneous_tuple,
    is_set,
    is_frozenset,
)

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from typing import Any, Protocol

    from gluetypes.predicates import TypePredicate

    type TypePathItem = str | int
    type TypePath = tuple[TypePathItem, ...]

    class LoaderProtocol(Protocol):
        def _load[T](
            self, value: Any, type_form: type[T], type_path: TypePath
        ) -> T: ...

    type TypeLoaderFn[T] = Callable[[Any, type[T], TypePath, LoaderProtocol], T]


__all__ = [
    "Loader",
]


def _load_simple_scalar[T](
    value: Any, type_form: type[T], type_path: TypePath, loader: LoaderProtocol
) -> T:
    if type(value) is type_form:
        return value
    raise GluetypesValueError(
        f"Cannot to load value {value!r} at path {type_path!r} into {type_form.__name___}"
    )


def _load_simple_sequence[T](
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


def _specialize_load_tuple[T](
    type_form: type[T],
    type_path: TypePath,
) -> str | None:
    """
    Generate specialized function for given type at given path.
    TODO: Specializer helper class based on ast + ast.unparse to generate code.
    """
    from gluetypes.predicates import get_args

    args = get_args(type_form)
    assert args is not None

    code = """\
def __specialized_fn(value, loader):
"""
    match args:
        case []:
            pass
        case [arg]:
            code += """\
    item_0, = value
"""
        case [*args]:
            code += f"""\
    {", ".join(f"item_{pos}" for pos in range(len(args)))} = value
"""
    code += """\
    _load = loader._load
    return (
"""
    for pos, arg in enumerate(args):
        type_path_str = repr((*type_path, pos))
        if type(arg) is not type:
            # Failed specialization
            return None
        code += f"""\
        _load(item_{pos}, {arg.__qualname__}, {type_path_str}),
"""
    code += """\
    )

"""
    return code


class SpecializingLoader:
    def __init__(self, loader, specializer) -> None:
        self._loader = loader
        self._specialized_loaders: dict = {}
        self._specializer = specializer
        self._threshold: int = 3

    def __call__[T](
        self,
        value: Any,
        type_form: type[T],
        type_path: TypePath,
        loader: LoaderProtocol,
    ) -> T:
        key = (type_form, type_path)
        specialized_loader = self._specialized_loaders.get(key)
        if type(specialized_loader) is type(None) or type(specialized_loader) is int:
            if type(specialized_loader) is int and specialized_loader > 0:
                count = specialized_loader + 1
            else:
                count = 1
            self._specialized_loaders[key] = count
            specialized_loader = None

            # Specialize!
            if count > self._threshold:
                specializer_fn_code = self._specializer(*key)
                if specializer_fn_code is None:
                    # zero means we can't specialize this
                    self._specialized_loaders[key] = 0
                else:
                    globals_ = {}
                    locals_ = {}

                    exec(specializer_fn_code, globals_, locals_)

                    specialized_loader = locals_["__specialized_fn"]
                    self._specialized_loaders[key] = specialized_loader

        if specialized_loader is None:
            return self._loader(value, type_form, type_path, loader)
        else:
            return specialized_loader(value, loader)


def _load_tuple[*Ts](
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


NoneType = type(None)


def _default_type_loaders():
    return {
        bool: _load_simple_scalar,
        int: _load_simple_scalar,
        float: _load_simple_scalar,
        str: _load_simple_scalar,
        NoneType: _load_simple_scalar,
    }


def _default_type_mappers(specialize: bool):
    # Note that the order matters as some predicates match several types,
    # put the most specific match first.
    return {
        is_homogeneous_tuple: _load_simple_sequence,
        is_tuple: SpecializingLoader(_load_tuple, _specialize_load_tuple)
        if specialize
        else _load_tuple,
        is_list: _load_simple_sequence,
        is_set: _load_simple_sequence,
        is_frozenset: _load_simple_sequence,
    }


class Loader:
    def __init__(
        self,
        type_loaders: Mapping[type, TypeLoaderFn] | None = None,
        type_mappers: Mapping[TypePredicate, TypeLoaderFn] | None = None,
        enable_specialization: bool = False,
    ) -> None:
        # Map a type to its loader
        if type_loaders is None:
            self._type_loaders: dict[type, TypeLoaderFn] = _default_type_loaders()
        else:
            self._type_loaders = dict(type_loaders)

        # Mapping of type predicate to a loader
        if type_mappers is None:
            self._type_mappers: Mapping[TypePredicate, TypeLoaderFn] = (
                _default_type_mappers(enable_specialization)
            )
        else:
            self._type_mappers = dict(type_mappers)

    def _load[T](self, value: Any, type_form: type[T], type_path: TypePath) -> T:
        if (type_loader := self._type_loaders.get(type_form)) is None:
            for type_predicate, type_loader in self._type_mappers.items():
                if type_predicate(type_form):
                    break
            else:
                type_loader = None
            if type_loader is None:
                raise GluetypesTypeError(
                    f"Unhandled type form {type_form!r} at path {type_path!r} for value {value!r}"
                )

            # Cache lookup for next time
            self._type_loaders[type_form] = type_loader

        try:
            return type_loader(value, type_form, type_path, self)  # type: ignore[call-non-callable]
        except GluetypesValueError:
            raise
        except Exception as e:
            error = GluetypesValueError(
                f"Failed to load value {value!r} at path {type_path!r} into type form {type_form!r}"
            )
            error.add_note(f"{type(e)}: {e}")
            raise error from e

    def load[T](self, value: Any, type_form: type[T]) -> T:
        return self._load(value, type_form, ())
