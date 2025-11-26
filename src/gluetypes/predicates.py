"""
Type predicates.

Do not import modules if not absolutely required. Instead, take advantage of the fact
that a type from a module can only be instantiated if it already has been imported.

For example to check if a type is an instance of foo.Bar, do not do:

    def is_foo_bar[T: type](type_form: T) -> bool:
        import foo

        return subclass(t, foo.Bar)

But instead:

    def is_foo_bar[T: type](type_form: T) -> bool:
        if foo := sys.modules.get("foo"):
            retur issubclass(t, foo.Bar)
"""

import sys

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    # TODO: Use actual typing.TypeForm once it has made its way into python.
    type TypeForm = Any

__all__ = [
    "get_origin",
    "get_args",
    "is_tuple",
    "is_homogeneous_tuple",
    "is_list",
    "is_set",
]

if TYPE_CHECKING:
    type TypePredicate[T: type] = Callable[[T], bool]

    __all__ += "TypePredicate"


def get_origin[T: TypeForm](type_form: T) -> type | None:
    # Avoid importing typing module if possible.
    # TODO: Handle annotated, generic etc...
    return getattr(type_form, "__origin__", None)


def get_args[T: TypeForm](type_form: T) -> tuple[type, ...] | None:
    # Avoid importing typing module if possible.
    # TODO: Handle annotated, generic etc...
    return getattr(type_form, "__args__", None)


def is_homogeneous_tuple[T: type](type_form: T) -> bool:
    """
    The given type form matches tuple[T, ...] or typing.Tuple[T, ...]
    """
    origin = get_origin(type_form)
    if origin is None:
        return False
    if origin is tuple or (
        (typing := sys.modules.get("typing")) and origin is typing.Tuple
    ):
        args = get_args(type_form)
        if args is None:
            return False
        return len(args) == 2 and args[1] == Ellipsis
    return False


def is_tuple[T: type](type_form: T) -> bool:
    origin = get_origin(type_form)
    if origin is None:
        return False
    if origin is tuple:
        return True
    if typing := sys.modules.get("typing"):
        return origin is typing.Tuple
    return False


def is_list[T: type](type_form: T) -> bool:
    origin = get_origin(type_form)
    if origin is None:
        return False
    if origin is list:
        return True
    if typing := sys.modules.get("typing"):
        return origin is typing.List
    return False


def is_set[T: type](type_form: T) -> bool:
    origin = get_origin(type_form)
    if origin is None:
        return False
    if origin is set:
        return True
    if typing := sys.modules.get("typing"):
        return origin is typing.Set
    return False


def is_frozenset[T: type](type_form: T) -> bool:
    origin = get_origin(type_form)
    if origin is None:
        return False
    if origin is frozenset:
        return True
    if typing := sys.modules.get("typing"):
        return origin is typing.FrozenSet
    return False
