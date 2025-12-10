"""
Dump the specified value to python basic types suitable for serialization.
Note that contrarily from Loader, the Dumper operates on concrete values and types.

Supports aliases.
"""

from tressed.exceptions import TressedTypeError, TressedValueError

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from typing import Any

    from tressed.alias import Alias, AliasFn, AliasResolver
    from tressed.dumper.types import Dumped, TypeDumperFn
    from tressed.predicates import TypePredicate
    from tressed.type_path import TypePath

__all__ = ["Dumper"]


def _default_type_dumpers() -> dict[type, TypeDumperFn]:
    from tressed.dumper.dumpers import (
        dump_complex,
        dump_identity,
        dump_simple_mapping,
        dump_simple_sequence,
    )

    return {
        str: dump_identity,
        int: dump_identity,
        float: dump_identity,
        bool: dump_identity,
        type(None): dump_identity,
        list: dump_simple_sequence,
        tuple: dump_simple_sequence,
        set: dump_simple_sequence,
        frozenset: dump_simple_sequence,
        dict: dump_simple_mapping,
        complex: dump_complex,
    }


def _default_type_mappers(specialize: bool) -> dict[TypePredicate, TypeDumperFn]:
    from tressed.dumper.dumpers import (
        dump_dataclass,
        dump_datetime,
        dump_enum,
        dump_fspath,
        dump_namedtuple,
        dump_simple_scalar,
    )
    from tressed.predicates import (
        is_dataclass_type,
        is_datetime_type,
        is_enum_type,
        is_fspath_type,
        is_ipaddress_type,
        is_namedtuple_type,
        is_uuid_type,
    )

    return {
        is_ipaddress_type: dump_simple_scalar,
        is_uuid_type: dump_simple_scalar,
        is_enum_type: dump_enum,
        is_datetime_type: dump_datetime,
        is_dataclass_type: dump_dataclass,
        is_namedtuple_type: dump_namedtuple,
        is_fspath_type: dump_fspath,
    }


class Dumper:
    def __init__(
        self,
        *,
        hide_defaults: bool = False,
        default_type_dumpers: Mapping[type, TypeDumperFn] | None = None,
        default_type_mappers: Mapping[TypePredicate, TypeDumperFn] | None = None,
        extra_type_dumpers: Mapping[type, TypeDumperFn] | None = None,
        extra_type_mappers: Mapping[TypePredicate, TypeDumperFn] | None = None,
        enable_specialization: bool = False,
        # If set enables alias lookup on fields, for example for dataclasses.
        alias_field: str | None = "alias",
        # Pass custom alias function, for example mapping field names to camelCase using to_camel.
        alias_fn: AliasFn | None = None,
        # Overriding the resolver factory allows for more advanced behavior like disablign caching,
        # or changing the alias resolution behavior entirely.
        alias_resolver_factory: Callable[[AliasFn | None], AliasResolver] | None = None,
    ) -> None:
        # Map a type to its dumper
        if default_type_dumpers is None:
            type_dumpers = _default_type_dumpers()
        else:
            type_dumpers = dict(default_type_dumpers)
        if extra_type_dumpers:
            type_dumpers |= extra_type_dumpers
        self._type_dumpers: dict[type, TypeDumperFn] = type_dumpers

        # Mapping of type predicate to a dumper
        if default_type_mappers is None:
            type_mappers = _default_type_mappers(enable_specialization)
        else:
            type_mappers = dict(default_type_mappers)
        if extra_type_mappers:
            type_mappers |= extra_type_mappers
        self._type_mappers: Mapping[TypePredicate, TypeDumperFn] = type_mappers

        from tressed.alias import (
            AliasResolver,
            compose_alias_fn,
            identity_alias_fn,
            make_maybe_dataclass_alias_fn,
        )

        if alias_field:
            alias_fn = compose_alias_fn(
                make_maybe_dataclass_alias_fn(alias_field=alias_field),
                alias_fn if alias_fn is not None else identity_alias_fn,
            )

        if alias_resolver_factory is None:
            self._alias_resolver = AliasResolver(alias_fn)
        else:
            self._alias_resolver = alias_resolver_factory(alias_fn)
        self.hide_defaults = hide_defaults

    def _resolve_alias(self, type_: type, type_path: TypePath, name: str) -> Alias:
        return self._alias_resolver.resolve(name, type_, type_path)

    def _dump(self, value: Any, type_path: TypePath) -> Dumped:
        type_: type = type(value)
        if (type_dumper := self._type_dumpers.get(type_)) is None:
            for type_predicate, type_dumper in self._type_mappers.items():
                if type_predicate(type_):
                    break
            else:
                type_dumper = None
            if type_dumper is None:
                raise TressedTypeError(value, type_path)

            # Cache lookup for next time
            self._type_dumpers[type_] = type_dumper

        try:
            return type_dumper(value, type_path, self)
        except TressedValueError:
            raise
        except Exception as e:
            # TODO: Different error for load and dump
            error = TressedValueError(value, type_, type_path)
            error.add_note(f"{type(e)}: {e}")
            raise error from e

    def dump(self, value: Any) -> Dumped:
        return self._dump(value, ())
