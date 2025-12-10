TYPE_CHECKING = False
if TYPE_CHECKING:
    from tressed.dumper.dumper import Dumper
    from tressed.dumper.types import Dumped, DumperFn, DumperProtocol

__all__ = ["Dumper", "Dumped", "DumperProtocol", "DumperFn"]


if not TYPE_CHECKING:

    def __getattr__(name: str):
        match name:
            case "Dumper":
                from tressed.dumper.dumper import Dumper

                return Dumper

            case "Dumped" | "DumperProtocol" | "DumperFn":
                from tressed.dumper import types

                return getattr(types, name)

            case _:
                raise AttributeError(
                    f"Package '{__package__}' has no attribute '{name}'"
                )
