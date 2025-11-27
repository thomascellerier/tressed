# TODO: Use python3.15+ lazy imports instead
# TODO: Switch to TypeForm https://peps.python.org/pep-0747/ once available
from __future__ import annotations

from gluetypes.exceptions import GluetypesTypeError, GluetypesValueError

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import Any

    from gluetypes.predicates import TypePredicate
    from gluetypes.loader.types import TypeLoaderFn, TypePath


__all__ = [
    "Loader",
]


def _default_type_loaders():
    from gluetypes.loader.loaders import load_simple_scalar

    return {
        bool: load_simple_scalar,
        int: load_simple_scalar,
        float: load_simple_scalar,
        str: load_simple_scalar,
        type(None): load_simple_scalar,
    }


def _default_type_mappers(specialize: bool) -> Mapping[TypePredicate, TypeLoaderFn]:
    from gluetypes.loader.loaders import load_simple_collection, load_tuple
    from gluetypes.predicates import (
        is_tuple,
        is_list,
        is_homogeneous_tuple,
        is_set,
        is_frozenset,
    )

    load_tuple_ = load_tuple
    load_simple_collection_ = load_simple_collection
    if specialize:
        from gluetypes.loader.specializer import SpecializingLoader
        from gluetypes.loader.specializers import (
            specialize_load_tuple,
            specialize_load_simple_collection,
        )

        load_tuple_ = SpecializingLoader(load_tuple, specialize_load_tuple)
        load_simple_collection_ = SpecializingLoader(
            load_simple_collection, specialize_load_simple_collection
        )

    # Note that the order matters as some predicates match several types,
    # put the most specific match first.
    return {
        is_homogeneous_tuple: load_simple_collection_,
        is_tuple: load_tuple_,
        is_list: load_simple_collection_,
        is_set: load_simple_collection_,
        is_frozenset: load_simple_collection_,
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
