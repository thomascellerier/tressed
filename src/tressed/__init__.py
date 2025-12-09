TYPE_CHECKING = False
if TYPE_CHECKING:
    from tressed.dumper.dumper import Dumper
    from tressed.loader.loader import Loader


__all__ = ["Loader", "Dumper"]


if not TYPE_CHECKING:

    def __getattr__(name: str) -> type[Loader] | type[Dumper]:
        match name:
            case "Loader":
                from tressed.loader.loader import Loader

                return Loader

            case "Dumper":
                from tressed.dumper.dumper import Dumper

                return Dumper

            case _:
                raise AttributeError(
                    f"Package '{__package__}' has no attribute '{name}'"
                )
