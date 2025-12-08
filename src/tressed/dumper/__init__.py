TYPE_CHECKING = False
if TYPE_CHECKING:
    from tressed.dumper.dumper import Dumper

__all__ = ["Dumper"]


def __getattr__(name: str) -> type[Dumper]:
    if name == "Dumper":
        from tressed.dumper.dumper import Dumper

        return Dumper

    raise AttributeError(f"Package 'tressed.dumper' has no attribute '{name}'")
