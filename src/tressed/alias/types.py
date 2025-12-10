TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Callable

    from tressed.type_form import TypeForm
    from tressed.type_path import TypePath

__all__ = [
    "Alias",
    "SimpleAliasFn",
    "TypeFormAliasFn",
    "TypePathAliasFn",
    "AliasFn",
]

type Alias = str
type SimpleAliasFn[AliasT = Alias] = Callable[[str], AliasT]
type TypeFormAliasFn[AliasT = Alias] = Callable[[str, TypeForm], AliasT]
type TypePathAliasFn[AliasT = Alias] = Callable[[str, TypeForm, TypePath], AliasT]
type AliasFn[AliasT = Alias] = (
    SimpleAliasFn[AliasT] | TypeFormAliasFn[AliasT] | TypePathAliasFn[AliasT]
)
