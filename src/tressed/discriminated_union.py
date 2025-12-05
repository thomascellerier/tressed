TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from typing import Any, Final, Literal

    from tressed.type_form import TypeForm


__all__ = ["Discriminator"]

if TYPE_CHECKING:
    type MatchFn = Callable[[Any, TypeForm], bool | int]
    type MatchStrategy = Literal["first-match", "best-match"]

    __all__ += ["MatchFn", "MatchStrategy"]


class Discriminator:
    __slots__ = ("match_fn", "strategy", "match")

    def __init__(
        self,
        match_fn: MatchFn,
        strategy: MatchStrategy = "first-match",
    ) -> None:
        self.match_fn: Final = match_fn
        self.strategy: Final = strategy
        match strategy:
            case "first-match":
                self.match = self.first_match
            case "best-match":
                self.match = self.best_match
            case _:
                assert False, f"Invalid match strategy {strategy}"

    def best_match(self, value: Any, *type_forms: TypeForm) -> TypeForm | None:
        best_matches: Sequence[TypeForm] = ()
        best_score = 0
        for type_form in type_forms:
            score = int(self.match_fn(value, type_form))
            if score < 1:
                continue
            if score > best_score:
                best_matches = (type_form,)
                best_score = score
            elif score == best_score:
                best_matches = (*best_matches, type_form)
        match best_matches:
            case [type_form]:
                return type_form
            case []:
                # no match
                return None
            case _:
                # ambiguous match
                return None

    def first_match(self, value: Any, *type_forms: TypeForm) -> TypeForm | None:
        for type_form in type_forms:
            if self.match_fn(value, type_form):
                return type_form
        return None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.match_fn=!r})"

    def __eq__(self, other: Any) -> bool:
        return type(self) is type(other) and self.match == other.match_fn

    def __hash__(self) -> int:
        return id(type(self)) + hash(self.match_fn) + hash(self.strategy)
