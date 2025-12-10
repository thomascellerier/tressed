TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Callable

    from tressed.type_form import TypeForm
    from tressed.type_path import TypePath


__all__ = [
    "AliasResolver",
    "normalize_alias_fn",
    "identity_alias_fn",
    "make_maybe_dataclass_alias_fn",
    "compose_alias_fn",
    "to_camel",
    "to_pascal",
]

if TYPE_CHECKING:
    type Alias = str
    type SimpleAliasFn[AliasT = Alias] = Callable[[str], AliasT]
    type TypeFormAliasFn[AliasT = Alias] = Callable[[str, TypeForm], AliasT]
    type TypePathAliasFn[AliasT = Alias] = Callable[[str, TypeForm, TypePath], AliasT]
    type AliasFn[AliasT = Alias] = (
        SimpleAliasFn[AliasT] | TypeFormAliasFn[AliasT] | TypePathAliasFn[AliasT]
    )

    __all__ += [
        "Alias",
        "SimpleAliasFn",
        "TypeFormAliasFn",
        "TypePathAliasFn",
        "AliasFn",
    ]


def normalize_alias_fn[AliasT = Alias](
    alias_fn: SimpleAliasFn[AliasT] | TypeFormAliasFn[AliasT] | AliasFn[AliasT],
) -> TypePathAliasFn[AliasT]:
    """
    Normalize alias fn to a type path alias fn.
    """
    # Avoid importing heavy inspect module, do some manual introspection
    arg_count = alias_fn.__code__.co_argcount
    if hasattr(alias_fn, "__self__"):
        # Bound method, substract the self argument
        arg_count -= 1

    match arg_count:
        case 3:
            return alias_fn  # type: ignore[return-value]
        case 2:

            def _type_form_alias_fn_wrapper(
                name: str, type_form: TypeForm, type_path: TypePath
            ) -> AliasT:
                return alias_fn(name, type_form)  # type: ignore[call-arg]

            return _type_form_alias_fn_wrapper
        case 1:

            def _simple_alias_fn_wrapper(
                name: str, type_form: TypeForm, type_path: TypePath
            ) -> AliasT:
                return alias_fn(name)  # type: ignore[call-arg]

            return _simple_alias_fn_wrapper
        case _:
            assert False, "unreachable"


def identity_alias_fn(name: str) -> str:
    return name


def _snake_to_camel_pascal(
    name: str, first_fn: Callable[[str], str], rest_fn: Callable[[str], str]
) -> str:
    # Find trailing dashes
    for index, char in enumerate(name):
        if char != "_":
            break

    parts = []
    end = len(name) - 1
    start = 0
    while start < end:
        index = name.find("_", index)

        # No more underscore, return rest
        if index < 0:
            break

        num_underscores = 1
        while index + 1 <= end and name[index + 1] == "_":
            index += 1
            num_underscores += 1

        # One underscore and more to come, remove underscore
        if num_underscores == 1 and index + 1 < end:
            parts.append(name[start:index].title())
        # More than one underscore or nothing more to come, preserve underscores as is
        else:
            parts.append(name[start : index + 1].title())
        index += 1
        start = index
    parts.append(name[start:])

    match parts:
        case [first, *parts]:
            return f"{first_fn(first)}{''.join(map(rest_fn, parts))}"
        case []:
            return ""
        case _:
            assert False, "unreachable"


def to_pascal(name: str) -> str:
    return _snake_to_camel_pascal(name, str.title, str.title)


def to_camel(name: str) -> str:
    return _snake_to_camel_pascal(name, str.lower, str.title)


def make_maybe_dataclass_alias_fn(alias_field: str) -> AliasFn[Alias | None]:
    def _maybe_dataclass_alias_fn(
        name: str, type_form: TypeForm, type_path: TypePath
    ) -> Alias | None:
        if fields := getattr(type_form, "__dataclass_fields__", None):
            field = fields[name]
            return field.metadata.get(alias_field)
        return None

    return _maybe_dataclass_alias_fn


def compose_alias_fn(
    *alias_fns: AliasFn[Alias | None],
    default_alias_fn: AliasFn[Alias] = identity_alias_fn,
) -> TypePathAliasFn:
    """
    Create an alias function by composing several alias functions.
    The functions are tried in order until an alias is returned.
    If none of the function match, the alias is resolved using the default alias function.
    """
    normalized_alias_fns = [normalize_alias_fn(alias_fn) for alias_fn in alias_fns]
    normalized_default_alias_fn = normalize_alias_fn(default_alias_fn)

    def _composed_alias_fn(
        name: str, type_form: TypeForm, type_path: TypePath
    ) -> Alias:
        for alias_fn in normalized_alias_fns:
            if (alias := alias_fn(name, type_form, type_path)) is not None:
                return alias
        return normalized_default_alias_fn(name, type_form, type_path)

    return _composed_alias_fn


class AliasResolver:
    def __init__(
        self, alias_fn: AliasFn | None = None, cache_resolved_aliases: bool = True
    ) -> None:
        if alias_fn is None:
            alias_fn = identity_alias_fn
        self._alias_fn = normalize_alias_fn(alias_fn)
        self._cache: dict[tuple[str, TypeForm, TypePath], Alias] = {}
        self.resolve = (
            self._resolve_cached if cache_resolved_aliases else self._alias_fn
        )

    def _resolve_cached(
        self, name: str, type_form: TypeForm, type_path: TypePath
    ) -> Alias:
        cache_key = (name, type_form, type_path)
        if (alias := self._cache.get(cache_key)) is not None:
            return alias

        alias = self._alias_fn(name, type_form, type_path)

        self._cache[cache_key] = alias
        return alias
