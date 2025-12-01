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

__all__ = [
    "get_origin",
    "get_args",
    "is_tuple_type",
    "is_homogeneous_tuple_type",
    "is_list_type",
    "is_set_type",
    "is_frozenset_type",
    "is_dataclass_type",
    "is_newtype",
]

if TYPE_CHECKING:
    # TODO: Use actual typing.TypeForm once it has made its way into python.
    # Experimental support is coming in mypy 1.19, the PEP (747) is not accepted yet as of the time of writing.
    type TypeForm = Any
    type TypePredicate[T: TypeForm] = Callable[[T], bool]

    __all__ += [
        "TypeForm",
        "TypePredicate",
    ]


def get_origin(type_form: TypeForm) -> type | None:
    # Avoid importing typing module if possible.
    # TODO: Handle annotated, generic etc...
    return getattr(type_form, "__origin__", None)


def get_args(type_form: TypeForm) -> tuple[type, ...] | None:
    # Avoid importing typing module if possible.
    # TODO: Handle annotated, generic etc...
    return getattr(type_form, "__args__", None)


def is_homogeneous_tuple_type(type_form: TypeForm) -> bool:
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


def is_tuple_type(type_form: TypeForm) -> bool:
    origin = get_origin(type_form)
    if origin is None:
        return False
    if origin is tuple:
        return True
    if typing := sys.modules.get("typing"):
        return origin is typing.Tuple
    return False


def is_list_type(type_form: TypeForm) -> bool:
    origin = get_origin(type_form)
    if origin is None:
        return False
    if origin is list:
        return True
    if typing := sys.modules.get("typing"):
        return origin is typing.List
    return False


def is_set_type(type_form: TypeForm) -> bool:
    origin = get_origin(type_form)
    if origin is None:
        return False
    if origin is set:
        return True
    if typing := sys.modules.get("typing"):
        return origin is typing.Set
    return False


def is_frozenset_type(type_form: TypeForm) -> bool:
    origin = get_origin(type_form)
    if origin is None:
        return False
    if origin is frozenset:
        return True
    if typing := sys.modules.get("typing"):
        return origin is typing.FrozenSet
    return False


def is_dataclass_type(type_form: TypeForm) -> bool:
    if dataclasses := sys.modules.get("dataclasses"):
        # We want to match only dataclass types, not instances
        return dataclasses.is_dataclass(type_form) and isinstance(type_form, type)
    return False


if sys.version_info >= (3, 10):

    def is_newtype(type_form: TypeForm) -> bool:
        if typing := sys.modules.get("typing"):
            return type(type_form) is typing.NewType
        return False
else:
    # NewType used to be a function, the only way to identify it
    # was to check for the __supertype__ attribute.
    def is_newtype(type_form: TypeForm) -> bool:
        return hasattr(type_form, "__supertype__")


def is_ipaddress_type(type_form: TypeForm) -> bool:
    if ipaddress := sys.modules.get("ipaddress"):
        return type_form in {
            ipaddress.IPv4Address,
            ipaddress.IPv6Address,
            ipaddress.IPv4Interface,
            ipaddress.IPv6Interface,
            ipaddress.IPv4Network,
            ipaddress.IPv6Network,
        }
    return False
