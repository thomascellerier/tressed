TYPE_CHECKING = False
if TYPE_CHECKING:
    from gluetypes.loader.loader import Loader

__all__ = ["Loader"]


def __getattr__(name: str) -> type[Loader]:
    if name == "Loader":
        from gluetypes.loader.loader import Loader

        return Loader

    raise AttributeError(f"Package 'gluetypes.loader' has no attribute '{name}'")
