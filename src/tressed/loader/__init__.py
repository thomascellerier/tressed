TYPE_CHECKING = False
if TYPE_CHECKING:
    from tressed.loader.loader import Loader

__all__ = ["Loader"]


if not TYPE_CHECKING:

    def __getattr__(name: str) -> type[Loader]:
        if name == "Loader":
            from tressed.loader.loader import Loader

            return Loader

        raise AttributeError(f"Package '{__package__}' has no attribute '{name}'")
