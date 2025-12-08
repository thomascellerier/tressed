TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, Protocol

    from tressed.type_path import TypePath

__all__ = []


if TYPE_CHECKING:
    __all__ += ["Dumped", "DumperProtocol", "TypeDumperFn"]

    # Dumped type, representing types that can be serialized to json out of the box.
    type Dumped = (
        int
        | float
        | str
        | bool
        | list[Dumped]
        | tuple[Dumped, ...]
        | dict[str, Dumped]
        | None
    )

    class DumperProtocol(Protocol):
        def _dump(self, value: Any, type_path: TypePath) -> Dumped: ...
        def _resolve_alias(
            self, value_type: type, type_path: TypePath, name: str
        ) -> str: ...

    type TypeDumperFn = Callable[[Any, TypePath, DumperProtocol], Dumped]
