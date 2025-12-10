TYPE_CHECKING = False
if TYPE_CHECKING:
    from tressed.loader.loader import Loader
    from tressed.loader.types import LoaderFn, LoaderProtocol

__all__ = ["Loader", "LoaderProtocol", "LoaderFn"]


if not TYPE_CHECKING:

    def __getattr__(name: str) -> type[Loader]:
        match name:
            case "Loader":
                from tressed.loader.loader import Loader

                return Loader

            case "LoaderProtocol" | "LoaderFn":
                from tressed.loader import types

                return getattr(types, name)

            case _:
                raise AttributeError(
                    f"Package '{__package__}' has no attribute '{name}'"
                )
