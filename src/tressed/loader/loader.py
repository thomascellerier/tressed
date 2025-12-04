# TODO: Use python3.15+ lazy imports instead
# TODO: Switch to TypeForm https://peps.python.org/pep-0747/ once available
from __future__ import annotations

from typing_extensions import TypeForm

from tressed.exceptions import TressedTypeError, TressedValueError

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from typing import Any

    from tressed.alias import Alias, AliasFn, AliasResolver
    from tressed.loader.types import TypeLoaderFn, TypePath
    from tressed.predicates import TypePredicate


__all__ = [
    "Loader",
]


def _default_type_loaders():
    from tressed.loader.loaders import load_complex, load_float, load_identity

    return {
        bool: load_identity,
        int: load_identity,
        float: load_float,
        str: load_identity,
        type(None): load_identity,
        complex: load_complex,
    }


def _default_type_mappers(specialize: bool) -> Mapping[TypePredicate, TypeLoaderFn]:
    from tressed.loader.loaders import (
        load_dataclass,
        load_dict,
        load_namedtuple,
        load_newtype,
        load_simple_collection,
        load_simple_scalar,
        load_tuple,
        load_typeddict,
    )
    from tressed.predicates import (
        is_dataclass_type,
        is_dict_type,
        is_frozenset_type,
        is_homogeneous_tuple_type,
        is_ipaddress_type,
        is_list_type,
        is_namedtuple_type,
        is_newtype,
        is_set_type,
        is_tuple_type,
        is_typeddict,
    )

    load_tuple_ = load_tuple
    load_simple_collection_ = load_simple_collection
    if specialize:
        from tressed.loader.specializer import SpecializingLoader
        from tressed.loader.specializers import (
            specialize_load_simple_collection,
            specialize_load_tuple,
        )

        load_tuple_ = SpecializingLoader(load_tuple, specialize_load_tuple)
        load_simple_collection_ = SpecializingLoader(
            load_simple_collection, specialize_load_simple_collection
        )

    # Note that the order matters as some predicates match several types,
    # put the most specific match first.
    return {
        is_homogeneous_tuple_type: load_simple_collection_,
        is_tuple_type: load_tuple_,
        is_list_type: load_simple_collection_,
        is_set_type: load_simple_collection_,
        is_frozenset_type: load_simple_collection_,
        is_dict_type: load_dict,
        is_newtype: load_newtype,
        is_typeddict: load_typeddict,
        is_dataclass_type: load_dataclass,
        is_ipaddress_type: load_simple_scalar,
        is_namedtuple_type: load_namedtuple,
    }


class Loader:
    def __init__(
        self,
        type_loaders: Mapping[TypeForm, TypeLoaderFn] | None = None,
        type_mappers: Mapping[TypePredicate, TypeLoaderFn] | None = None,
        enable_specialization: bool = False,
        # If set enables alias lookup on fields, for example for dataclasses.
        alias_field: str | None = "alias",
        # Pass custom alias function, for example mapping field names to camelCase using to_camel.
        alias_fn: AliasFn | None = None,
        # Overriding the resolver factory allows for more advanced behavior like disablign caching,
        # or changing the alias resolution behavior entirely.
        alias_resolver_factory: Callable[[AliasFn | None], AliasResolver] | None = None,
    ) -> None:
        # Map a type to its loader
        if type_loaders is None:
            self._type_loaders: dict[TypeForm, TypeLoaderFn] = _default_type_loaders()
        else:
            self._type_loaders = dict(type_loaders)

        # Mapping of type predicate to a loader
        if type_mappers is None:
            self._type_mappers: Mapping[TypePredicate, TypeLoaderFn] = (
                _default_type_mappers(enable_specialization)
            )
        else:
            self._type_mappers = dict(type_mappers)

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

    def _resolve_alias[T](
        self, type_form: TypeForm, type_path: TypePath, name: str
    ) -> Alias:
        return self._alias_resolver.resolve(name, type_form, type_path)

    def _load[T](self, value: Any, type_form: TypeForm[T], type_path: TypePath) -> T:
        if (type_loader := self._type_loaders.get(type_form)) is None:
            for type_predicate, type_loader in self._type_mappers.items():
                if type_predicate(type_form):
                    break
            else:
                type_loader = None
            if type_loader is None:
                raise TressedTypeError(
                    f"Unhandled type form {type_form!r} at path {type_path!r} for value {value!r}"
                )

            # Cache lookup for next time
            self._type_loaders[type_form] = type_loader

        try:
            return type_loader(value, type_form, type_path, self)
        except TressedValueError:
            raise
        except Exception as e:
            error = TressedValueError(
                f"Failed to load value {value!r} at path {type_path!r} into type form {type_form!r}"
            )
            error.add_note(f"{type(e)}: {e}")
            raise error from e

    def load[T](self, value: Any, type_form: TypeForm[T]) -> T:
        return self._load(value, type_form, ())
