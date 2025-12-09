TYPE_CHECKING = False
if TYPE_CHECKING:
    from tressed.dumper.dumper import Dumper

__all__ = ["Dumper"]


if not TYPE_CHECKING:

    def __getattr__(name: str) -> type[Dumper]:
        if name == "Dumper":
            from tressed.dumper.dumper import Dumper

            return Dumper

        raise AttributeError(f"Package '{__package__}' has no attribute '{name}'")
