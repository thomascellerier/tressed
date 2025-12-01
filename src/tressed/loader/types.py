__all__ = []

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, Protocol

    from typing_extensions import TypeForm

    type TypePathItem = str | int
    type TypePath = tuple[TypePathItem, ...]

    class LoaderProtocol(Protocol):
        def _load[T](
            self, value: Any, type_form: TypeForm[T], type_path: TypePath
        ) -> T: ...
        def _resolve_alias[T](
            self, type_form: TypeForm[T], type_path: TypePath, name: str
        ) -> str: ...

    type TypeLoaderFn[T] = Callable[[Any, TypeForm[T], TypePath, LoaderProtocol], T]
    type TypeLoaderSpecializer[T] = Callable[[TypeForm[T], TypePath], str | None]

    __all__ += [
        "TypePathItem",
        "TypePath",
        "LoaderProtocol",
        "TypeLoaderFn",
        "TypeLoaderSpecializer",
    ]
