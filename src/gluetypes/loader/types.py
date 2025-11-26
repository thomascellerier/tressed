__all__ = []

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, Protocol

    type TypePathItem = str | int
    type TypePath = tuple[TypePathItem, ...]

    class LoaderProtocol(Protocol):
        def _load[T](
            self, value: Any, type_form: type[T], type_path: TypePath
        ) -> T: ...

    type TypeLoaderFn[T] = Callable[[Any, type[T], TypePath, LoaderProtocol], T]

    __all__ += [
        "TypePathItem",
        "TypePath",
        "LoaderProtocol",
        "TypeLoaderFn",
    ]
