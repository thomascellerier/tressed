__all__ = ["__version__"]

TYPE_CHECKING = False
if TYPE_CHECKING:
    __version__: str


def __getattr__(name: str) -> str:
    if name == "__version__":
        from importlib.metadata import version

        return version("tressed")
    raise AttributeError(f"Package '{__package__}' has no attribute '{name}'")
