TYPE_CHECKING = False
if TYPE_CHECKING:
    from tressed.dumper.dumper import Dumper
    from tressed.loader.loader import Loader


__all__ = ["Loader", "Dumper", "load", "dump"]


if TYPE_CHECKING:
    _default_loader = Loader()
    load = _default_loader.load

    _default_dumper = Dumper()
    dump = _default_dumper.dump

else:

    def __getattr__(name: str) -> type[Loader] | type[Dumper]:
        match name:
            case "Loader":
                from tressed.loader.loader import Loader

                return Loader

            case "Dumper":
                from tressed.dumper.dumper import Dumper

                return Dumper

            case "load":
                if "_default_loader" not in globals():
                    global _default_loader
                    from tressed.loader.loader import Loader

                    _default_loader = Loader()
                return _default_loader.load

            case "dump":
                if "_default_dumper" not in globals():
                    global _default_dumper
                    from tressed.dumper.dumper import Dumper

                    _default_dumper = Dumper()
                return _default_dumper.dump

            case _:
                raise AttributeError(
                    f"Package '{__package__}' has no attribute '{name}'"
                )
