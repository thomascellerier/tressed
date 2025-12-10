__all__ = [
    "Alias",
    "AliasFn",
    "AliasResolver",
    "to_identity",
    "to_camel",
    "to_pascal",
    "compose_alias_fn",
    "make_maybe_dataclass_alias_fn",
]

TYPE_CHECKING = False
if TYPE_CHECKING:
    from tressed.alias.functions import (
        compose_alias_fn,
        make_maybe_dataclass_alias_fn,
        to_camel,
        to_identity,
        to_pascal,
    )
    from tressed.alias.resolver import AliasResolver
    from tressed.alias.types import Alias, AliasFn


else:

    def __getattr__(name: str):
        match name:
            case "Alias" | "AliasFn":
                from tressed.alias import types

                return getattr(types, name)

            case "AliasResolver":
                from tressed.alias import resolver

                return getattr(resolver, name)

            case (
                "compose_alias_fn"
                | "make_maybe_dataclass_alias_fn"
                | "to_identity"
                | "to_camel"
                | "to_pascal"
            ):
                from tressed.alias import functions

                return getattr(functions, name)

            case _:
                raise AttributeError(
                    f"Package '{__package__}' has no attribute '{name}'"
                )
