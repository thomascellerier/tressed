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

    from tressed.type_form import TypeForm

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
    "is_typeddict",
    "is_dict_type",
    "is_namedtuple_type",
    "is_uuid_type",
    "is_enum_type",
    "is_literal_type",
    "is_type_alias_type",
    "is_optional_type",
    "is_union_type",
    "is_fspath_type",
    "is_datetime_type",
    "is_discriminated_union",
]

if TYPE_CHECKING:
    type TypePredicate[T: TypeForm] = Callable[[T], bool]

    __all__ += [
        "TypeForm",
        "TypePredicate",
    ]


def get_origin(type_form: TypeForm) -> TypeForm | None:
    # Avoid importing typing module if possible.
    # TODO: Handle annotated, generic etc...
    return getattr(type_form, "__origin__", None)


def get_args(type_form: TypeForm) -> tuple[TypeForm, ...] | None:
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


def is_typeddict(type_form: TypeForm) -> bool:
    if typing := sys.modules.get("typing"):
        if typing.is_typeddict(type_form):
            return True
    if typing_extensions := sys.modules.get("typing_extensions"):
        if typing_extensions.is_typeddict(type_form):
            return True
    return False


def is_dict_type(type_form: TypeForm) -> bool:
    origin = get_origin(type_form)
    if origin is dict:
        return True
    elif (typing := sys.modules.get("typing")) and origin is typing.Dict:
        return True
    return False


def is_namedtuple_type(type_form: TypeForm) -> bool:
    if (typing := sys.modules.get("typing")) and (
        orig_bases := getattr(type_form, "__orig_bases__", None)
    ):
        return typing.NamedTuple in orig_bases
    return False


def is_uuid_type(type_form: TypeForm) -> bool:
    if uuid := sys.modules.get("uuid"):
        return type_form is uuid.UUID
    return False


def is_enum_type(type_form: TypeForm) -> bool:
    if enum := sys.modules.get("enum"):
        return type(type_form) is enum.EnumType
    return False


def is_literal_type(type_form: TypeForm) -> bool:
    if typing := sys.modules.get("typing"):
        return get_origin(type_form) is typing.Literal
    return False


def is_type_alias_type(type_form: TypeForm) -> bool:
    return hasattr(type_form, "__type_params__") and hasattr(
        type_form, "evaluate_value"
    )


def is_optional_type(type_form: TypeForm) -> bool:
    """
    One of:
        T | None
        typing.Optional[T]
    """
    origin = get_origin(type_form)
    if origin is None:
        return False

    args = get_args(type_form)
    if args is None:
        return False

    num_args = len(args)
    if num_args == 2:
        if type(None) in args:
            import types

            if origin is types.UnionType:
                return True

            if typing := sys.modules.get("typing"):
                return origin is typing.Union

    elif num_args == 1 and (typing := sys.modules.get("typing")):
        return origin is typing.Optional

    return False


def is_union_type(type_form: TypeForm) -> bool:
    origin = get_origin(type_form)
    args = get_args(type_form)
    if not args:
        # A union needs at least one argument
        return False

    import types

    if origin is types.UnionType:
        return True

    if typing := sys.modules.get("typing"):
        return origin is typing.Union
    return False


def is_fspath_type(type_form: TypeForm) -> bool:
    return hasattr(type_form, "__fspath__")


def is_datetime_type(type_form: TypeForm) -> bool:
    if datetime := sys.modules.get("datetime"):
        return type_form in frozenset({datetime.datetime, datetime.date, datetime.time})
    return False


def is_discriminated_union(type_form: TypeForm) -> bool:
    """
    A discriminated union is a union annotated by one discriminator.
    """
    if not hasattr(type_form, "__metadata__"):
        return False

    if discriminated_union := sys.modules.get("tressed.discriminated_union"):
        args = get_args(type_form)
        assert args
        (arg,) = args
        if not is_union_type(arg):
            return False

        num_discriminators = sum(
            1
            for metadata in type_form.__metadata__
            if isinstance(metadata, discriminated_union.Discriminator)
        )
        return num_discriminators == 1
    return False
