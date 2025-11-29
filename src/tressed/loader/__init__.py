TYPE_CHECKING = False
if TYPE_CHECKING:
    from tressed.loader.loader import Loader

__all__ = ["Loader"]


def __getattr__(name: str) -> type[Loader]:
    if name == "Loader":
        from tressed.loader.loader import Loader

        return Loader

    raise AttributeError(f"Package 'tressed.loader' has no attribute '{name}'")
