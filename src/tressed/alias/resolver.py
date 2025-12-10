TYPE_CHEKCING = False
if TYPE_CHEKCING:
    from tressed.alias.types import Alias, AliasFn
    from tressed.type_form import TypeForm
    from tressed.type_path import TypePath

__all__ = ["AliasResolver"]


class AliasResolver:
    def __init__(
        self, alias_fn: AliasFn | None = None, cache_resolved_aliases: bool = True
    ) -> None:
        from tressed.alias.functions import normalize_alias_fn, to_identity

        if alias_fn is None:
            alias_fn = to_identity
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
